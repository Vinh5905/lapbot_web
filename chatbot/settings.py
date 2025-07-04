"""
Django settings for chatbot project.

Generated by 'django-admin startproject' using Django 5.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import dotenv
import os

dotenv.load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-+uhb)49mm2!qyhuw+c6$etbv=87xvwdifc&11_%%4_1jk3w3(!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
# if RENDER_EXTERNAL_HOSTNAME:
#     ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Application definition

INSTALLED_APPS = [
    # Deploy
    'whitenoise.runserver_nostatic', # Phải ở trên cùng

    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Deploy
    'corsheaders', # Thêm corsheaders

    # Custom apps
    'core',
    'chat',
    'userauths',
    
    # Library
    'django_cotton',
    'tailwind',
    'django_browser_reload',
    # 'theme',
    'django_vite'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Đặt ngay sau SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Đặt trước CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = 'chatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Nếu có template ở thư mục gốc dự án
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True, # Cho phép Django tìm template trong thư mục 'templates' của mỗi app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Global variables
                'core.context_processors.global_variables',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
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

# LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True # Kích hoạt hệ thống dịch thuật/quốc tế hóa
# USE_L10N = True # Kích hoạt hệ thống định dạng
# USE_THOUSAND_SEPARATOR = True # Cho phép sử dụng dấu phân cách hàng nghìn

USE_TZ = True

# LANGUAGE_CODE = 'vi'  # Ngôn ngữ của trang web


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'vite_assets',
]

# Cấu hình cho django-vite
#    Đường dẫn đến thư mục chứa kết quả build của Vite (nơi có manifest.json).
DJANGO_VITE_ASSETS_PATH = BASE_DIR / "vite_assets"
#    Tự động bật/tắt chế độ dev của Vite dựa trên DEBUG của Django.
DJANGO_VITE_DEV_MODE = os.environ.get('DEBUG', 'False').lower() == 'true'

# # Tối ưu hóa việc lưu trữ của Whitenoise
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Components
COTTON_DIR = 'components'
COTTON_SNAKE_CASED_NAMES = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
     # Welcome text on the login screen
    "welcome_sign": "Welcome to Kevin's Laptop Chatbot Admin Site ❤️",

    # Copyright on the footer
    "copyright": "Kevin Pham Laptop Chatbot",
}

AUTH_USER_MODEL = 'userauths.User'

# TAILWINCSS NAME
# TAILWIND_APP_NAME = 'theme'

DJANGO_VITE = {
    "default": {
        "dev_mode": True
    }
}

# Cung cấp một giá trị mặc định cho môi trường development.
INTERNAL_API_BASE_URL = os.getenv('INTERNAL_API_BASE_URL', 'http://localhost:8000')