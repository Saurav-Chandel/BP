from json import dumps

import requests
from django.core.mail import send_mail
from rest_framework import status
from app.response import ResponseBadRequest
from beachplus import settings



def send_reset_password_mail(request, user_email, email_body):
    """
    Send Reset Password Mail
    """

    if user_email and email_body:
        Message = email_body
        from_email = settings.EMAIL_HOST_USER
        to_email = user_email
        try:
            send_mail(
                "Reset your passsword<Don't Reply>",
                Message,
                from_email,
                [to_email],
                fail_silently=False,
            )
        except Exception as e:
            return e
    return None