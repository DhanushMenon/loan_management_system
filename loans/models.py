from dateutil.relativedelta import relativedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("user", "User"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_email_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)  # Ensuring email is required and unique

    def __str__(self):
        return self.username


# Loan Model
class Loan(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("CLOSED", "Closed"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loans")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(1000, message="Minimum loan amount is ₹1,000"),
            MaxValueValidator(100000, message="Maximum loan amount is ₹100,000"),
        ],
    )
    tenure = models.PositiveIntegerField(
        validators=[
            MinValueValidator(3, message="Minimum tenure is 3 months"),
            MaxValueValidator(24, message="Maximum tenure is 24 months"),
        ]
    )
    interest_rate = models.FloatField()  # Annual interest rate in percentage
    monthly_installment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_interest = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_loan(self):
        yearly_rate = self.interest_rate
        monthly_rate = yearly_rate / 12 / 100
        n = self.tenure

        if monthly_rate == 0:
            emi = self.amount / n
        else:
            emi = float(self.amount) * monthly_rate * pow(1 + monthly_rate, n)
            emi /= (pow(1 + monthly_rate, n) - 1)

        self.monthly_installment = round(Decimal(emi), 2)
        self.total_amount = round(Decimal(emi * n), 2)
        self.total_interest = self.total_amount - self.amount

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.monthly_installment:
            self.calculate_loan()
        super().save(*args, **kwargs)

        # Generate payment schedule only for new loans
        if is_new:
            self.create_payment_schedule()

    def create_payment_schedule(self):
        existing_payments = Payment.objects.filter(loan=self).exists()
        if existing_payments:
            return

        monthly_installment = self.monthly_installment
        start_date = self.created_at.date()

        for i in range(1, self.tenure + 1):
            due_date = start_date + relativedelta(months=i)
            Payment.objects.create(
                loan=self,
                installment_number=i,
                due_date=due_date,
                amount=monthly_installment,
                status="PENDING",
            )

    def get_payment_schedule(self):
        return self.payments.all().order_by("due_date")

    def get_total_paid(self):
        return self.payments.filter(status="PAID").aggregate(total=models.Sum("paid_amount"))["total"] or Decimal(0)

    def get_amount_remaining(self):
        return self.total_amount - self.get_total_paid()

    def get_next_payment(self):
        return self.payments.filter(status="PENDING").order_by("due_date").first()

    def update_loan_status(self):
        if self.get_total_paid() >= self.total_amount:
            self.status = "CLOSED"
            self.save()

    def __str__(self):
        return f"Loan {self.id} - {self.user.username} - ₹{self.amount}"


# OTP Model
class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        return (timezone.now() - self.created_at).total_seconds() <= 600

    def __str__(self):
        return f"OTP for {self.email} - {'Verified' if self.is_verified else 'Pending'}"


# Payment Model
class Payment(models.Model):
    PAYMENT_STATUS = (
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    )

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="payments")
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="PENDING")
    paid_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["due_date"]
        unique_together = ("loan", "installment_number")

    def __str__(self):
        return f"Payment {self.installment_number} for Loan {self.loan.id}"

    def mark_as_paid(self, paid_amount, paid_date=None):
        self.status = "PAID"
        self.paid_amount = paid_amount
        self.paid_date = paid_date or timezone.now().date()
        self.save()

        # Update loan status after payment
        self.loan.update_loan_status()

    def check_if_overdue(self):
        if self.status == "PENDING" and self.due_date < timezone.now().date():
            self.status = "OVERDUE"
            self.save()
