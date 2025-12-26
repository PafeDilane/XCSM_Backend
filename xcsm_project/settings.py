"""
Django settings for xcsm_project.

Backend XCSM – configuration développement
Django 5.2.x
MySQL via XAMPP (connexion TCP)

Ce fichier combine les configurations des deux fichiers sources,
avec une sécurité optimale pour l'environnement de développement.
"""

from pathlib import Path
import os

# ================================================================
# CONFIGURATION DE BASE ET CHEMINS
# ================================================================

# BASE_DIR : Définit le chemin absolu vers le répertoire parent du fichier settings.py
# Cette variable est essentielle pour construire des chemins relatifs dans le projet
BASE_DIR = Path(__file__).resolve().parent.parent


# ================================================================
# SÉCURITÉ ET ENVIRONNEMENT DE DÉVELOPPEMENT
# ================================================================

# SECRET_KEY : Clé cryptographique utilisée pour signer les sessions, tokens, etc.
# IMPORTANT : Ne jamais exposer cette clé en production
# À changer en production avec une clé sécurisée et unique
SECRET_KEY = 'django-insecure-2bap)$_(%6z#=zfz373mh49ot743=60!kiy%xh)!^rd2q&a43w'

# DEBUG : Active le mode débogage pour le développement
# En développement : True
# En production : toujours False
DEBUG = True

# ALLOWED_HOSTS : Liste des domaines/noms d'hôte autorisés
# En développement : liste vide ou ['localhost', '127.0.0.1']
# En production : spécifier explicitement les domaines
ALLOWED_HOSTS = []


# ================================================================
# APPLICATIONS INSTALLÉES
# ================================================================

INSTALLED_APPS = [
    # Applications natives de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Application métier principale
    'xcsm',

    # Applications tierces
    'rest_framework',
    'corsheaders',
    'drf_yasg',
]


# ================================================================
# MIDDLEWARE
# ================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # Middleware CORS (doit être placé avant CommonMiddleware)
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ================================================================
# CONFIGURATION CORS
# ================================================================

# Autorise toutes les origines en développement
# En production, restreindre explicitement
CORS_ALLOW_ALL_ORIGINS = True


# ================================================================
# DJANGO REST FRAMEWORK
# ================================================================

REST_FRAMEWORK = {
    # Permissions par défaut pour toutes les vues API
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# ================================================================
# URLS ET TEMPLATES
# ================================================================

ROOT_URLCONF = 'xcsm_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Point d’entrée WSGI
WSGI_APPLICATION = 'xcsm_project.wsgi.application'


# ================================================================
# BASE DE DONNÉES (MySQL via XAMPP ou MariaDB System version recente (supérieure ou égale à 10.5 pour compatibilité avec la version actuelle de Django)+ PhpMyAdmin Independant installé pour gestionnaire GUI
# ================================================================

DATABASES = {
    'default': {
        # Moteur MySQL/MariaDB pour XAMPP
        'ENGINE': 'django.db.backends.mysql',

        # Nom de la base
        'NAME': 'xcsm_db',

        # Utilisateur MySQL dédié
        'USER': 'xcsm_admin',

        # Mot de passe MySQL
        'PASSWORD': 'xcsm.4gi.enspy27',

        # Connexion TCP requise pour XAMPP/
        'HOST': '127.0.0.1',

        # Port MySQL standard
        'PORT': '3306',

        # Options MySQL
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# ================================================================
# VALIDATION DES MOTS DE PASSE
# ================================================================

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


# ================================================================
# INTERNATIONALISATION
# ================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True


# ================================================================
# FICHIERS STATIQUES ET MÉDIAS
# ================================================================

# Templates
TEMPLATES[0]['DIRS'] = [BASE_DIR / "templates"]

# Static
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ================================================================
# CONFIGURATION DES MODÈLES
# ================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'xcsm.Utilisateur'

# ================================================================
# CONFIGURATION JWT
# ================================================================

INSTALLED_APPS += [
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Pour logout
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour',
        'anon': '100/day',
    }
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    # Claims personnalisés
    'TOKEN_OBTAIN_SERIALIZER': 'xcsm.serializers.CustomTokenObtainPairSerializer',
}

