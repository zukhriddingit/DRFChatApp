from django.core.mail import send_mail
from django.conf import settings
import random
import string
import redis
from django.conf import settings
from django.core.mail import send_mail


def send_chat_message_email(to_email, subject, message):
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [to_email],
        fail_silently=False,
    )


redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)


def generate_verification_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# def send_verification_email(email, code):
#     subject = 'Your verification code'
#     message = f'Your verification code is {code}'
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = [email]
#     send_mail(subject, message, from_email, recipient_list)


def store_verification_code(email, code):
    redis_client.setex(f'verification_code:{email}', 120, code)
