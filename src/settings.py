"""
Django settings for src project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from sqlalchemy import create_engine

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'otbz(=^xy4g4tsp%o2m+q@63t=ms7ujb7uo0k8sxy*w4_l^r9f'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ifrs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CACHES = {
    'default': {
        'TIMEOUT': None,
    }
}

ROOT_URLCONF = 'src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'templates',
            'ifrs/templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'ifrs_db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'


# IFRS project settings

CHUNK_ROOT = os.path.join(BASE_DIR, 'chunk')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


UPLOAD_FILE_TYPES = (
    'vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'vnd.ms-excel.sheet.binary.macroenabled.12',
)
UPLOAD_FILE_EXTENSIONS = (
    '.xlsx',
    '.xlsb',
)
EXCEL_ENGINE = {
    '.xlsx': 'xlrd',
    '.xlsb': 'pyxlsb',
}
# Паттерны имен загружаемых excel файлов.
UPLOAD_FILE_NAMES = (
    '[R][C][P]\s[0][1][.][0][1-9][.][2][0]\d\d',
    '[R][C][P]\s[0][1][.][1][0-2][.][2][0]\d\d',
)
# Максимальный размер загружаемого файла excel. По умолчанию равен 55MB.
MAX_UPLOAD_SIZE = 55 * 1048576
# Минимальное количество строк в портфеле, чтобы признать его валидным.
MIN_ROWS_IN_EXCEL_FILE = 200000
FROM_EXCEL_TO_UNIX_TIMESTAMP_DELTA = 25569
RCP_DATABASE_NAME = 'ifrs_db'
SQL_ENGINE = create_engine(f'sqlite:///{RCP_DATABASE_NAME}.sqlite3')
FIELD_TITLES = (
    'contract_number',
    'contract_type',
    'contract_date',
    'credit_limit',
    'accrued_interest_balance',
    'accrued_interest_off_balance',
    'contract_rate',
    'current_rate',
    'product_id',
    'debt',
    'overdue_duration',
    'npl',
    'write_off_debt',
    'total_debt',
)
FIELD_TITLES_RUS = (
    'НОМЕР ДОГОВОРА',
    'ТИП ДОГОВОРА',
    'ДАТА ЗАКЛЮЧЕНИЯ ДОГОВОРА',
    'ЛИМИТ ВЫДАЧИ',
    'НАРАЩ. %%, БАЛАНС',
    'НАРАЩ. %%, ЗАБАЛАНС',
    '%% НА ДАТУ ВЫДАЧИ',
    '%% НА ОТЧ. ДАТУ',
    'ID ВАРИАНТ',
    'ЗАДОЛЖ.',
    'ПРОДОЛЖ. ПРОСР.',
    'NPL',
    'СПИС. ЗАДОЛЖ.',
    'ОБЩАЯ ЗАДОЛЖ.',
)
EXPECTED_DATA_TYPES = {
    'contract_number': 'object',
    'contract_type': 'object',
    'contract_date': 'datetime64[ns]',
    'credit_limit': 'float64',
    'accrued_interest_balance': 'float64',
    'accrued_interest_off_balance': 'float64',
    'contract_rate': 'float64',
    'current_rate': 'float64',
    'product_id': 'object',
    'debt': 'float64',
    'overdue_duration': 'int64',
    'npl': 'object',
    'write_off_debt': 'float64',
    'total_debt': 'float64',
}
# Коды продуктов для включения в доп. выборку, по которым ведется работа ООО "Правовой диалог".
LGD_PROGRAM_INCLUDE = 'OV_PS|OV_BD|OV_NK|OV_SUPER|OV_BD_CASH'
# Коды программ для исключения из доп. выборки.
LGD_PROGRAM_EXCLUDE = 'OV_PS_NIS|OV_PS_TR|OV_PS_FORD|OV_PS_AV'
# Коэффициенты взымаемые правовым диалогом по программам кредитования. "Выборочные программы" -
# часть продуктов категории "Банковские карты", по которым ведется работа ООО "Правовой диалог".
COMISSION_COEFS = {
    'Автокредит': [0, 0, 0],
    'Кредит на недвижимость': [0, 0, 0],
    'Потребительское кредитование': [0, 0, 0],
    'Delay': [0.08, 0.12, 0.2],
    'Банковские карты': [0, 0, 0],
    'Выборочные программы': [0.078, 0.105, 0.19],
}