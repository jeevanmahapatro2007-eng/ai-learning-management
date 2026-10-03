"""
Django settings for the Lodestar Personalized AI-Based Learning
Management System.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this-secret-key-before-deploying-lodestar'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Lodestar apps
    'apps.users',
    'apps.core',
    'apps.courses',
    'apps.quizzes',
    'apps.recommendations',
    'apps.analytics',
    'apps.dashboard',
    'apps.notifications',
    'apps.gamification',
    'apps.administration',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notifications.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Dev default: print password-reset emails to the runserver console instead of
# trying (and failing) to reach an SMTP server. Override for production.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'Lodestar <no-reply@lodestar.local>'

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'dashboard:redirect'
LOGOUT_REDIRECT_URL = 'core:home'

MESSAGE_TAGS = {
    10: 'debug',
    20: 'info',
    25: 'success',
    30: 'warning',
    40: 'error',
}

# ---------------------------------------------------------------------------
# Lodestar-specific settings for the recommendation engine
# ---------------------------------------------------------------------------
LODESTAR_SKILL_LEVELS = ['Beginner', 'Intermediate', 'Advanced']
LODESTAR_PASS_MARK_PERCENT = 60
LODESTAR_WEAK_TOPIC_THRESHOLD = 50  # % below which a topic is "weak"
