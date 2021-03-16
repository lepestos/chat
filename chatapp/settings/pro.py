from .base import *


DEBUG = False

ADMINS = (
    ('Kirill N', 'kirillnazarov1928@gmail.com'),
)

ALLOWED_HOSTS = ['chatproject.com', 'www.chatproject.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chatapp',
        'USER': 'chatapp',
        'PASSWORD': '315317725',
    }
}

SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
