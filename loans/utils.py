import random
import string
from django.core.mail import send_mail
from django.conf import settings
import socket

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via SMTP"""
    subject = 'Email Verification OTP'
    message = f'''
    Your OTP for email verification is: {otp}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this, please ignore this email.
    '''
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        print(f"Attempting to resolve {settings.EMAIL_HOST}")
        socket.gethostbyname(settings.EMAIL_HOST)

        print(f"Using email settings:")
        print(f"HOST: {settings.EMAIL_HOST}")
        print(f"PORT: {settings.EMAIL_PORT}")
        print(f"TLS: {settings.EMAIL_USE_TLS}")
        print(f"FROM: {settings.EMAIL_HOST_USER}")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        return False
