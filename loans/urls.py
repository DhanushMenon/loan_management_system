from django.urls import path, include
from rest_framework.routers import DefaultRouter

from loans.views import (
    RegisterUserView,
    LoginView,
    verify_email,
    resend_otp,
    LoanViewSet,
)

#Creation of router and viewset
router = DefaultRouter()
router.register(r'loans', LoanViewSet, basename='loan')


urlpatterns = [
    path('auth/register/', RegisterUserView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/verify-email/', verify_email, name='verify-email'),
    path('auth/resend-otp/', resend_otp, name='resend-otp'),
    path('', include(router.urls)),  # Include the router URLs
]
