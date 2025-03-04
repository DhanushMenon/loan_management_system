from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from loans.models import Loan, OTP, Payment

User = get_user_model()


# User Registration Serializer
# User Registration Serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role")

    def create(self, validated_data):
        # Default role is "user"
        role = validated_data.get("role", "user")

        # Only allow setting "admin" if the requesting user is an admin
        request = self.context.get("request")
        if role == "admin" and (not request or not request.user.is_authenticated or request.user.role != "admin"):
            raise serializers.ValidationError({"error": "Only admins can create other admin accounts."})

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=role,  # Set role based on validation
        )
        return user


# User Login Serializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user = User.objects.filter(username=data["username"]).first()

        if not user or not user.check_password(data["password"]):
            raise serializers.ValidationError({"error": "Invalid username or password"})

        refresh = RefreshToken.for_user(user)
        user = User.objects.get(id=user.id)  # Ensure correct role is fetched

        return {
            "refresh": "Bearer " + str(refresh),  # ✅ Add "Bearer" prefix
            "access": "Bearer " + str(refresh.access_token),  # ✅ Add "Bearer" prefix
            "role": user.role,
        }



# OTP Verification Serializer
class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        if not OTP.objects.filter(email=data["email"], otp=data["otp"], is_verified=False).exists():
            raise serializers.ValidationError({"error": "Invalid OTP or already verified."})
        return data


# Email Serializer for OTP Resend
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoanSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)  # ✅ Ensure amount is Decimal
    tenure = serializers.IntegerField()  # ✅ Ensure tenure is an Integer

    class Meta:
        model = Loan
        fields = "__all__"
        read_only_fields = [
            "user",
            "monthly_installment",
            "total_interest",
            "total_amount",
            "status",
        ]

    def validate_amount(self, value):
        """Ensure loan amount is between ₹1,000 and ₹100,000."""
        if value < 1000 or value > 100000:
            raise serializers.ValidationError("Loan amount must be a number between ₹1,000 and ₹100,000.")
        return value

    def validate_tenure(self, value):
        """Ensure tenure is a whole number between 3 and 24 months."""
        if value < 3 or value > 24:
            raise serializers.ValidationError("Loan tenure must be a whole number between 3 and 24 months.")
        return value


# Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "installment_number",
            "due_date",
            "amount",
            "status",
            "paid_date",
            "paid_amount",
        ]
        read_only_fields = [
            "installment_number",
            "due_date",
            "amount",
            "status",
            "paid_date",
            "paid_amount",
        ]
