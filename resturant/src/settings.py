from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-umami-sushi-x^_xh)93_a4#x6_j(gro6r=ji!'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Telegram — User Bot (mijozlar uchun)
USER_BOT_TOKEN = os.getenv('USER_BOT_TOKEN', '8793577525:AAG4a3pqO9prPMJkGXnMU2CKnFnLeCh0xDY')
USER_BOT_USERNAME = os.getenv('USER_BOT_USERNAME', 'amina_suhsi_order_bot')

# Telegram — Staff Bot (admin uchun)
STAFF_BOT_TOKEN = os.getenv('STAFF_BOT_TOKEN', '8714192126:AAGBazzW_xPuk6pT5eT5gNbOKnlx0R278eM')
STAFF_BOT_USERNAME = os.getenv('STAFF_BOT_USERNAME', 'umami_staff_bot')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '6830116501'))

# Kassir Chat Bot — mijozlar bilan chat
CASHIER_BOT_TOKEN = os.getenv('CASHIER_BOT_TOKEN', '')
CASHIER_CHAT_ADMIN_IDS = [int(x.strip()) for x in os.getenv('CASHIER_CHAT_ADMIN_IDS', '6830116501').split(',')]

SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')
