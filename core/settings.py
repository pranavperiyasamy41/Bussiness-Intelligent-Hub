
"""
Django settings for core project.
This file is now ready for production.
"""

from pathlib import Path
import os  # <-- ADD THIS IMPORT
import dj_database_url  # <-- ADD THIS IMPORT
from dotenv import load_dotenv  # <-- ADD THIS IMPORT

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- THIS IS NEW ---
# Load all the variables from our .env file (SECRET_KEY, GOOGLE_AI_API_KEY, etc.)
load_dotenv(BASE_DIR / '.env')
# --- END NEW ---


# --- THIS IS NO LONGER HARD-CODED ---
# It now safely reads from your .env file
SECRET_KEY = os.environ.get('SECRET_KEY')

# --- THIS IS NEW ---
# Reads the 'ENVIRONMENT' variable from your .env file
# If 'production', DEBUG is False. If 'development', DEBUG is True.
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
DEBUG = (ENVIRONMENT == 'development')
# --- END NEW ---

ALLOWED_HOSTS = ['*']

# --- THIS IS NEW (For Render) ---
# Render will tell us what our website's URL is
# e.g., 'bi-hub.onrender.com'
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# --- END NEW ---


# Application definition

INSTALLED_APPS = [
    'hub',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'hub.context_processors.analysis_history', # This is our custom one
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# --- NEW PRODUCTION DATABASE ---
# This code will use PostgreSQL if it's on Render (production)
# or stick with SQLite if it's on your laptop (development).
DATABASES = {
    'default': dj_database_url.config(
        # This is the default for your laptop
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}
# --- END NEW DATABASE ---


# Password validation (Unchanged)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization (Unchanged)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# --- NEW STATICFILES CONFIG FOR PRODUCTION ---
# This is required by Render
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
# --- END NEW ---

# Media files (User Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type (Unchanged)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- THIS IS NO LONGER HARD-CODED ---
# It now safely reads from your .env file
GOOGLE_AI_API_KEY = os.environ.get('GOOGLE_AI_API_KEY')

# --- This tells @login_required where to send users.
LOGIN_URL = 'login'
