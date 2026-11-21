"""
Django settings for Faheem project.
Enterprise-grade modular architecture.
"""

from pathlib import Path
import os
import sys
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Add BASE_DIR to Python path for app discovery
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-_ssq=w3$d9(rp2yc(hke*0do6jlh#i^5y5zaii8sqdm9p77)om'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000', 'http://127.0.0.1:3000']),
    TELEGRAM_BOT_TOKEN=(str, ''),
    TELEGRAM_WEBHOOK_SECRET=(str, ''),
    TELEGRAM_ADMIN_CHAT_ID=(str, ''),
    TELEGRAM_ADMIN_PASSCODE=(str, 'FaheemAdmin2026'),
    GOOGLE_ACCOUNT_EMAIL=(str, ''),
    GOOGLE_DRIVE_ROOT_FOLDER_ID=(str, '1S2Gyrk8cWTQoOALM1YBYL6fTUEigAmTe'),
    GOOGLE_SERVICE_ACCOUNT_FILE=(str, 'credentials.json'),
)

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.academic.apps.AcademicConfig',
    'apps.drive_sync.apps.DriveSyncConfig',
    'apps.ingestion.apps.IngestionConfig',
    'apps.telegram_bot.apps.TelegramBotConfig',
    'apps.operations.apps.OperationsConfig',
    'apps.api.apps.ApiConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

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

WSGI_APPLICATION = 'project.wsgi.application'

# Database configuration
DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Damascus'
USE_I18N = True
USE_TZ = True

# Static & Media Files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True

# Custom Faheem Integration Settings
FAHEEM_CONFIG = {
    'GOOGLE_ACCOUNT_EMAIL': env('GOOGLE_ACCOUNT_EMAIL'),
    'GOOGLE_DRIVE_ROOT_FOLDER_ID': env('GOOGLE_DRIVE_ROOT_FOLDER_ID'),
    'GOOGLE_SERVICE_ACCOUNT_FILE': BASE_DIR / env('GOOGLE_SERVICE_ACCOUNT_FILE'),
    'TELEGRAM_BOT_TOKEN': env('TELEGRAM_BOT_TOKEN'),
    'TELEGRAM_WEBHOOK_SECRET': env('TELEGRAM_WEBHOOK_SECRET'),
    'TELEGRAM_ADMIN_CHAT_ID': env('TELEGRAM_ADMIN_CHAT_ID'),
    'TELEGRAM_ADMIN_PASSCODE': env('TELEGRAM_ADMIN_PASSCODE', default='FaheemAdmin2026'),
    'INGESTION_TEMP_DIR': BASE_DIR / env('INGESTION_TEMP_DIR', default='media/ingestion'),
}
