import os
import sys
from pathlib import Path

# --------------------------------------------------------------------------------------
# Paths and runtime environment
# --------------------------------------------------------------------------------------
SOURCE_BASE_DIR = Path(__file__).resolve().parent.parent  # project root (source)
FROZEN = getattr(sys, "frozen", False)
MEIPASS_DIR = Path(getattr(sys, "_MEIPASS", SOURCE_BASE_DIR))  # PyInstaller extraction dir

# Where assets (templates/static) are read from at runtime
RUNTIME_ASSETS_ROOT = MEIPASS_DIR if FROZEN else SOURCE_BASE_DIR

# --------------------------------------------------------------------------------------
# Writable data directory (DB, media, etc.) – safe per OS and packaging
# --------------------------------------------------------------------------------------
def default_data_dir(app="Calculator"):
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    return base / app

# Prefer your app's function if available; otherwise fall back to a safe default
try:
    from calculator.licenseing import get_data_dir as _get_dd
except Exception:
    _get_dd = None

DATA_DIR = Path((_get_dd() if _get_dd else default_data_dir())).expanduser()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------------------
# Core Django settings
# --------------------------------------------------------------------------------------
SECRET_KEY = 'django-insecure-)z-k8&$xxmp_pg5s1kv0x12)8qg(7t*)c_dxxty!o3!2fn1t7a'
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# If you post to the dev server from the browser, these help avoid CSRF issues locally
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8765",
    "http://localhost:8765",
]

# --------------------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# Templates
# When frozen, templates are included in the bundle and extracted under sys._MEIPASS.
# --------------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [RUNTIME_ASSETS_ROOT / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# --------------------------------------------------------------------------------------
# Database (SQLite stored in user-writable DATA_DIR)
# --------------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATA_DIR / "calculator.sqlite3"),
    }
}

# --------------------------------------------------------------------------------------
# Password validation
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# Internationalization / Time
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# Ensure tzdata is referenced so PyInstaller bundles it on Windows (no-op otherwise)
try:
    import tzdata  # noqa: F401
except Exception:
    pass

# --------------------------------------------------------------------------------------
# Static and media files
# - STATICFILES_DIRS points to bundled static when frozen
# - MEDIA_ROOT uses DATA_DIR so it's writable in packaged builds
# --------------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [RUNTIME_ASSETS_ROOT / 'static']
STATIC_ROOT = SOURCE_BASE_DIR / 'static_root'  # if you ever run collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR / 'media'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Optional app-specific media path
PROJECT_IMAGES_DIR = 'project_images'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------------------
# App-specific defaults
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# Licensing public key
# --------------------------------------------------------------------------------------
LICENSE_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJU91mU/KwhAlRGHn3ic
LLVgk52ptb/1hh0rz3TZvU3O67gzBNZL+fT/ffaqMEe6SqCPwOlIlSOwXTF9mJVt
bosqAXzKA+vm0b0172kMhFi386n89RcMLiDw8FqnZvKBoLFGi7mv7TXOzp7uQe5L
PsFsNrBIHairGGBKZJy8PQWVJYxuR4EEJLqEk/o1DWzyEpsEcS+RdFcf7GV9SHFi
RqL4WEErxx+3ZIHW6AWl4ahaeobdyHctHC2fkshoSqssxjFuJ0DmhK6Xsw5Suklw
DOPENK8XhU+6Vn2t7q59PTVv3QJBZHAehEY9+pXaG9Q/fHR74bq8UBdDPiJsECTj
bwIDAQAB
-----END PUBLIC KEY-----"""
