import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.groups',
    'apps.students',
    'apps.finance',
    'apps.reports',
    'apps.attendance',
    'apps.messaging',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scholarly.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'scholarly.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME',     'scholarly_db'),
        'USER':     os.getenv('DB_USER',     'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST':     os.getenv('DB_HOST',     'localhost'),
        'PORT':     os.getenv('DB_PORT',     '5432'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N = True
USE_TZ   = True

STATIC_URL   = '/static/'
STATIC_ROOT  = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/login/'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# SMS: dry_run (standart, yubormaydi) | console (logging) | webhook (tashqi URL)
SMS_BACKEND = os.getenv('SMS_BACKEND', 'dry_run').strip().lower()
SMS_WEBHOOK_URL = os.getenv('SMS_WEBHOOK_URL', '').strip()
SMS_WEBHOOK_SECRET = os.getenv('SMS_WEBHOOK_SECRET', '').strip()
