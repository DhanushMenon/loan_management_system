from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from .models import Loan, OTP, Payment, User
from .serializers import UserSerializer, LoginSerializer, LoanSerializer, OTPVerificationSerializer, EmailSerializer, \
    PaymentSerializer
from .utils import generate_otp, send_otp_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal

User = get_user_model()

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get("role", "user")  # Default to user
        user = serializer.save(role=role)

        otp_code = generate_otp()
        OTP.objects.create(email=user.email, otp=otp_code)
        send_otp_email(user.email, otp_code)

        return Response({"message": "Registration successful. Verify your email with OTP.", "user_id": user.id},
                        status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    request_body=OTPVerificationSerializer,
    responses={
        200: openapi.Response("Email verified successfully"),
        400: openapi.Response("Invalid OTP or OTP expired"),
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify Email with OTP"""
    serializer = OTPVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp']

    try:
        otp_obj = OTP.objects.filter(email=email, otp=otp_code, is_verified=False).latest('created_at')
        if not otp_obj.is_valid():
            return Response({"message": "OTP expired. Request a new one."}, status=400)

        user = User.objects.get(email=email)
        user.is_email_verified = True
        user.save()
        otp_obj.is_verified = True
        otp_obj.save()

        return Response({"message": "Email verified successfully"})
    except OTP.DoesNotExist:
        return Response({"message": "Invalid OTP"}, status=400)

@swagger_auto_schema(
    method='post',
    request_body=EmailSerializer,
    responses={
        200: openapi.Response("OTP sent successfully"),
        400: openapi.Response("User not found or email already verified"),
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Resend OTP to the given email"""
    serializer = EmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email=email)
        if user.is_email_verified:
            return Response({"message": "Email already verified"}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = generate_otp()
        OTP.objects.create(email=email, otp=otp_code)
        send_otp_email(email, otp_code)

        return Response({"message": "OTP sent successfully"})
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


from rest_framework.exceptions import PermissionDenied

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Loan.objects.none()  # Return empty for unauthenticated users

        # 🔹 Ensure `role` is retrieved correctly from the database
        user = User.objects.get(id=self.request.user.id)

        if user.role == "admin":
            return Loan.objects.all()  # Admin can see all loans
        return Loan.objects.filter(user=user)  # Users see only their loans

    def perform_create(self, serializer):
        """Assign the logged-in user to the loan."""
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        loan = self.get_object()

        # 🔹 Ensure only admins can delete loans
        if not request.user.is_authenticated or request.user.role != "admin":
            return Response({"detail": "Only admins can delete loans."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(loan)
        return Response(status=status.HTTP_204_NO_CONTENT)

    from decimal import Decimal  # Import Decimal

    @action(detail=True, methods=['post'])
    def foreclose(self, request, pk=None):
        """ Allows users to foreclose (pay off) their loan early """
        loan = self.get_object()

        if loan.status == "CLOSED":
            return Response({"message": "Loan already closed"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert everything to Decimal to avoid float-Decimal conflict
        total_paid = Decimal(loan.get_total_paid())  # Ensure Decimal
        remaining_principal = Decimal(loan.amount) - total_paid  # Ensure Decimal
        remaining_interest = Decimal(loan.get_amount_remaining()) - remaining_principal  # Ensure Decimal
        foreclosure_discount = remaining_interest * Decimal("0.05")  # Ensure Decimal
        final_settlement = remaining_principal + (remaining_interest - foreclosure_discount)  # Ensure Decimal

        # Mark loan as closed
        loan.status = "CLOSED"
        loan.save()

        # Create final payment entry
        Payment.objects.create(
            loan=loan,
            installment_number=loan.payments.count() + 1,
            due_date=timezone.now().date(),
            amount=final_settlement,
            status='PAID',
            paid_date=timezone.now().date(),
            paid_amount=final_settlement
        )

        return Response({
            "loan_id": f"LOAN{loan.id}",
            "foreclosure_discount": float(foreclosure_discount),  # Convert to float for response
            "final_settlement": float(final_settlement),  # Convert to float for response
            "status": loan.status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def make_payment(self, request, pk=None):
        loan = self.get_object()

        # Prevent payments on closed loans
        if loan.status == "CLOSED":
            return Response({"message": "This loan is already closed. No further payments allowed."},
                            status=status.HTTP_400_BAD_REQUEST)

        payment = loan.get_next_payment()
        if not payment:
            return Response({"message": "No pending payments found"}, status=status.HTTP_400_BAD_REQUEST)

        amount = Decimal(request.data.get('amount', 0))
        if amount < payment.amount:
            return Response({"message": f"Payment must be at least {payment.amount}"},
                            status=status.HTTP_400_BAD_REQUEST)

        payment.mark_as_paid(amount)
        loan.update_loan_status()

        return Response({
            "message": "Payment successful",
            "amount_paid": float(payment.paid_amount),
            "remaining_balance": float(loan.get_amount_remaining()),
        })

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        loan = self.get_object()
        payment_schedule = loan.get_payment_schedule()  # This returns a queryset
        serialized_payments = PaymentSerializer(payment_schedule, many=True).data  # Serialize the queryset

        return Response({
            "loan_id": f"LOAN{loan.id}",
            "loan_details": {
                "amount": float(loan.amount),
                "tenure": loan.tenure,
                "status": loan.status,
                "created_at": loan.created_at,
            },
            "payment_summary": {
                "total_amount": float(loan.total_amount),
                "amount_paid": float(loan.get_total_paid()),
                "amount_remaining": float(loan.get_amount_remaining()),
                "next_payment_date": loan.get_next_payment().due_date if loan.get_next_payment() else None,
            },
            "payment_schedule": serialized_payments,  # Use serialized data
        })
