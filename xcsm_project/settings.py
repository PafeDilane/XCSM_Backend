"""
Configuration Django pour le projet xcsm_project.

Ce fichier gère les paramètres globaux de l'application XCSM, incluant la base de données,
la sécurité, l'authentification JWT et les tâches asynchrones Celery.
Les variables sensibles sont chargées depuis un fichier .env via django-environ.
"""
import sys
from pathlib import Path
import os
from datetime import timedelta
import environ

# Initialisation de django-environ pour la gestion des variables d'environnement
env = environ.Env(
    DEBUG=(bool, False),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
    USE_MONGODB=(bool, True),
    USE_REDIS=(bool, False),
)

# Dossier de base du projet (contient manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Chargement explicite du fichier .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ================================================================
# SÉCURITÉ ET ENVIRONNEMENT
# ================================================================

# Clé secrète Django (doit être gardée secrète en production)
SECRET_KEY = env('SECRET_KEY', default='django-insecure-default-key-change-it')

# Mode débogage (True en dev, False en production)
DEBUG = env('DEBUG')

# Domaines autorisés à communiquer avec l'API
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


# ================================================================
# APPLICATIONS INSTALLÉES
# ================================================================

INSTALLED_APPS = [
    # Cœur de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Application métier XCSM (Extraction et Gestion de Contenu)
    'xcsm',

    # Librairies tierces essentielles
    'rest_framework',           # Framework pour l'API REST
    'corsheaders',              # Gestion du Cross-Origin Resource Sharing
    'drf_yasg',                 # Documentation automatique (Swagger/ReDoc)
    'rest_framework_simplejwt', # Authentification par tokens JWT
    'rest_framework_simplejwt.token_blacklist', # Gestion de la déconnexion (blacklist)
]


# ================================================================
# FILTRES INTERMÉDIAIRES (MIDDLEWARE)
# ================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Placé en haut pour gérer les requêtes cross-origin
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ================================================================
# CONFIGURATION CORS (Cross-Origin Resource Sharing)
# ================================================================

# En développement, on autorise tout. En production, configurer CORS_ALLOWED_ORIGINS dans le .env
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=True)


# ================================================================
# DJANGO REST FRAMEWORK (DRF)
# ================================================================

REST_FRAMEWORK = {
    # On force l'authentification par JWT pour toute l'API
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Par défaut, toutes les vues demandent d'être authentifié
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Limitation du nombre de requêtes (Anti-DDoS / Rate Limiting)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour', # 1000 requêtes par heure pour un utilisateur connecté
        'anon': '100/day',   # 100 requêtes par jour pour les anonymes
    },
    # Gestionnaire d'erreurs personnalisé pour l'examen
    'EXCEPTION_HANDLER': 'xcsm.exceptions.custom_exception_handler',
}


# ================================================================
# URLS ET TEMPLATES
# ================================================================

ROOT_URLCONF = 'xcsm_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'xcsm_project.wsgi.application'


# ================================================================
# BASES DE DONNÉES (MySQL/MariaDB)
# ================================================================

DATABASES = {
    # Connexion principale via variable DATABASE_URL ou paramètres individuels
    'default': env.db('DATABASE_URL', default=f"mysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('DB_HOST')}:{env('DB_PORT')}/{env('DB_NAME')}"),
}

# Configuration du nom de la base de test
DATABASES['default']['TEST'] = {
    'NAME': env('TEST_DB_NAME', default='test_xcsm_db'),
}

# Choix dynamique du moteur de base de données pour les tests (MySQL ou SQLite)
# Par défaut, SQLite est utilisé pour sa rapidité. Définir DB_ENGINE_TEST=mysql dans le .env pour tester sur MySQL.
if 'test' in sys.argv or 'pytest' in sys.argv[0]:
    if env('DB_ENGINE_TEST', default='sqlite') != 'mysql':
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3.test',
        }
    # Si 'mysql' est choisi, on conserve la configuration DATABASES['default'] définie plus haut


# ================================================================
# SÉCURITÉ ET COOKIES (Production vs Dev)
# ================================================================

X_FRAME_OPTIONS = 'DENY' # Empêche d'inclure l'API dans un <iframe> (sécurité clickjacking)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    # Paramètres de sécurité stricts pour la production
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000 # Force HTTPS pendant 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "same-origin"


# ================================================================
# INTERNATIONALISATION ET LOCALISATION
# ================================================================

LANGUAGE_CODE = 'fr-fr' # Application en Français
TIME_ZONE = 'Africa/Douala' # Fuseau horaire du Cameroun
USE_I18N = True
USE_TZ = True


# ================================================================
# FICHIERS STATIQUES ET MÉDIAS
# ================================================================

# Fichiers statiques (CSS, JS, Images du site)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Fichiers médias (Documents PDF/DOCX uploadés par les profs)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modèle utilisateur personnalisé (étend les capacités de base de Django)
AUTH_USER_MODEL = 'xcsm.Utilisateur'


# ================================================================
# CONFIGURATION JWT (Simple JWT)
# ================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(env('JWT_ACCESS_TOKEN_LIFETIME', default=60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(env('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7))),
    'ROTATE_REFRESH_TOKENS': True,      # Renouvelle le refresh token à chaque usage
    'BLACKLIST_AFTER_ROTATION': True,   # Invalide les anciens tokens après rotation
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': env('JWT_ALGORITHM', default='HS256'),
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'xcsm.serializers.CustomTokenObtainPairSerializer',
}

# ================================================================
# CONFIGURATION MONGODB (Stockage des Granules et Documents)
# ================================================================
MONGO_SETTINGS = {
    'URI': env('MONGO_URI', default='mongodb://localhost:27017/'),
    'DB_NAME': env('MONGO_DB_NAME', default='xcsm_granules_db'),
}

# ================================================================
# CONFIGURATION CELERY / REDIS (Tâches asynchrones)
# ================================================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_TIMEZONE = TIME_ZONE


# ================================================================
# CONFIGURATION LOGGING (Traçabilité)
# ================================================================
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'xcsm_debug.log'),
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'xcsm_errors.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'error_file'], 'level': 'INFO', 'propagate': True},
        'xcsm': {'handlers': ['console', 'file', 'error_file'], 'level': 'DEBUG', 'propagate': True},
        'celery': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': True},
    },
}

# ================================================================
# CONFIGURATION EMAIL (SMTP)
# ================================================================
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=1025)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='XCSM <noreply@xcsm.local>')

