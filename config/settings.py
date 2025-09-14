import os
from pathlib import Path
from calculator.licenseing import get_data_dir

BASE_DIR = Path(__file__).resolve().parent.parent

# Safe default; overridden if licenseing is importable
DATA_DIR = Path.home() / ".local" / "share" / "Calculator"

try:
    from calculator.licenseing import get_data_dir as _get_dd
    DATA_DIR = Path(_get_dd())
except Exception:
    # During PyInstaller analysis or if jose isn’t importable here,
    # fall back to a writable path so the hook doesn’t crash.
    pass

os.makedirs(DATA_DIR, exist_ok=True)

SECRET_KEY = 'django-insecure-)z-k8&$xxmp_pg5s1kv0x12)8qg(7t*)c_dxxty!o3!2fn1t7a'

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'calculator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "calculator.middleware.LicenseRequiredMiddleware",
]

ROOT_URLCONF = 'config.urls'

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


TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]
TEMPLATES[0]["APP_DIRS"] = True


WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(DATA_DIR, "calculator.sqlite3"),
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'static_root')
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Create media directory structure
PROJECT_IMAGES_DIR = 'project_images'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom settings for the calculator
DEFAULT_SETTINGS = {
    'filament_density': 1.24,
    'filament_diameter': 1.75,
    'electricity_cost_per_kwh': 1000,
    'printer_power': 0.15,
    'printer_depreciation_per_hour': 500,
    'post_processing_base_cost': 5000,
    'painting_cost_per_cm3': 250,
    'profit_margin': 70
}

LICENSE_PUBLIC_KEY_PEM ="""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJU91mU/KwhAlRGHn3ic
LLVgk52ptb/1hh0rz3TZvU3O67gzBNZL+fT/ffaqMEe6SqCPwOlIlSOwXTF9mJVt
bosqAXzKA+vm0b0172kMhFi386n89RcMLiDw8FqnZvKBoLFGi7mv7TXOzp7uQe5L
PsFsNrBIHairGGBKZJy8PQWVJYxuR4EEJLqEk/o1DWzyEpsEcS+RdFcf7GV9SHFi
RqL4WEErxx+3ZIHW6AWl4ahaeobdyHctHC2fkshoSqssxjFuJ0DmhK6Xsw5Suklw
DOPENK8XhU+6Vn2t7q59PTVv3QJBZHAehEY9+pXaG9Q/fHR74bq8UBdDPiJsECTj
bwIDAQAB
-----END PUBLIC KEY-----"""