# 📦 Structure du Projet XCSM Backend (poussée avec config sup)

## 🗂️ Architecture Complète Commentée

```
XCSM_Backend/
│
├── 📁 env/                           # Environnement virtuel Python (ignoré par Git)
│   ├── bin/                         # Scripts d'activation
│   ├── lib/                         # Bibliothèques installées
│   └── pyvenv.cfg                   # Configuration de l'environnement
│
├── 📁 xcsm_project/                 # Configuration principale Django
│   ├── __init__.py                  # Package Python
│   ├── settings.py                  # ⚙️ Configuration du projet (importe .env)
│   ├── urls.py                      # 🌐 Routes principales
│   ├── wsgi.py                      # 🚀 Interface WSGI pour production
│   ├── asgi.py                      # ⚡ Interface ASGI pour async
│   └── celery.py                    # 🎯 Configuration Celery pour tâches async
│
├── 📁 xcsm/                         # Application principale (logique métier)
│   ├── migrations/                  # 📋 Migrations de base de données
│   │   ├── __init__.py
│   │   └── *.py                     # Fichiers de migration auto-générés
│   │
│   ├── tests/                       # 🧪 Tests automatisés
│   │   ├── __init__.py
│   │   ├── test_models.py           # Tests des modèles
│   │   ├── test_views.py            # Tests des vues API
│   │   ├── test_processing.py       # Tests du traitement document
│   │   └── test_integration.py      # Tests d'intégration
│   │
│   ├── __init__.py                  # Package Python
│   ├── admin.py                     # 👨‍💼 Interface d'administration Django
│   ├── apps.py                      # ⚙️ Configuration de l'application
│   ├── models.py                    # 🗃️ Modèles de données (MySQL)
│   ├── views.py                     # 🎮 Vues API (controllers)
│   ├── serializers.py               # 🔄 Sérialiseurs DRF (Python ↔ JSON)
│   ├── urls.py                      # 🛣️ Routes de l'application
│   ├── permissions.py               # 🔐 Permissions et contrôle d'accès
│   ├── processing.py                # ⚙️ Moteur de traitement des documents
│   └── utils.py                     # 🛠️ Fonctions utilitaires réutilisables
│
├── 📁 media/                        # 📁 Fichiers uploadés par les utilisateurs
│   ├── documents_bruts/             # 📄 Documents originaux avant traitement
│   └── photos_profil/               # 👤 Images de profil (futur)
│
├── 📁 staticfiles/                  # 🎨 Fichiers statiques collectés (CSS, JS, images)
│   └── admin/                       # Fichiers statiques de l'admin Django
│
├── 📁 static/                       # 💎 Fichiers statiques source
│   └── css/                         # Styles CSS personnalisés
│
├── 📁 resultats/                    # 📊 Résultats de traitement (fallback)
│   └── *.json                       # Fichiers JSON générés
│
├── 📁 logs/                         # 📝 Logs système
│   ├── xcsm_backend.log             # Log principal de l'application
│   ├── xcsm_errors.log              # Log des erreurs
│   └── xcsm_access.log              # Log d'accès HTTP
│
├── 📁 scripts/                      # 📜 Scripts utilitaires
│   ├── test_json_processing.py      # 🧪 Script de test du traitement
│   ├── init-db.sql                  # 🗄️ Script d'initialisation MySQL
│   └── backup.sh                    # 💾 Script de sauvegarde (futur)
│
├── 📁 config/                       # ⚙️ Fichiers de configuration sensibles
│   └── firebase-credentials.json    # 🔥 Credentials Firebase (notifications)
│
├── 📁 backups/                      # 💾 Sauvegardes automatiques (optionnel)
│   └── 2025-12-20/                  # Dossiers par date
│
├── .env                            # 🔐 Variables d'environnement (IGNORÉ par Git)
├── .env.example                    # 📋 Template des variables d'environnement
├── requirements.txt                # 📦 Dépendances Python complètes
├── requirements-dev.txt            # 🔧 Dépendances développement (optionnel)
├── setup-local-env.sh              # 🚀 Script de configuration automatique
├── manage.py                       # 🛠️ CLI Django (commandes manage.py)
├── README.md                       # 📖 Documentation principale
├── MIGRATION_JSON.md               # 📄 Documentation technique migration JSON
├── docker-compose.yml              # 🐳 Configuration Docker (futur)
└── .gitignore                      # 🚫 Fichiers ignorés par Git
```

## 🔧 Fichier `.env.example` (Template)

```env
# ============================================
# XCSM BACKEND - ENVIRONMENT VARIABLES TEMPLATE
# ============================================
# Auteur: Team XCSM 4GI-ENSPY Promo 2027
# Date: Décembre 2025
# ============================================

# =======================
# DJANGO CONFIGURATION
# =======================
# Clé secrète pour Django (générer avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
SECRET_KEY=votre_super_secret_key_ici_50_caracteres_minimum

# Mode débogage - À METTRE À False EN PRODUCTION
DEBUG=True

# Hôtes autorisés à se connecter
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Paramètres régionaux
TIME_ZONE=Africa/Douala
LANGUAGE_CODE=fr-fr

# =======================
# DATABASE CONFIGURATION (MySQL)
# =======================
# Configuration MySQL pour les métadonnées structurées
DB_ENGINE=mysql
DB_NAME=xcsm_db
DB_USER=xcsm_admin
DB_PASSWORD=votre_mot_de_passe_mysql_ici
DB_HOST=localhost
DB_PORT=3306

# Pool de connexions
DB_MAX_CONNECTIONS=20
DB_CONN_MAX_AGE=300

# =======================
# MONGODB CONFIGURATION
# =======================
# Configuration MongoDB pour le contenu non-structuré et les granules
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=xcsm_granules_db
MONGO_USERNAME=xcsm_mongo_admin
MONGO_PASSWORD=votre_mot_de_passe_mongodb_ici
MONGO_AUTH_SOURCE=admin
MONGO_AUTH_MECHANISM=SCRAM-SHA-256
USE_MONGODB=True

# Paramètres de connexion MongoDB
MONGO_MAX_POOL_SIZE=10
MONGO_MIN_POOL_SIZE=2

# =======================
# REDIS CONFIGURATION
# =======================
# Configuration Redis pour le cache et Celery
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=votre_mot_de_passe_redis_ici
REDIS_DATABASE=0
USE_REDIS=True

# Paramètres de connexion Redis
REDIS_MAX_CONNECTIONS=10
REDIS_CACHE_TTL_GENERAL=300  # en secondes

# =======================
# CELERY CONFIGURATION
# =======================
# Configuration Celery pour les tâches asynchrones
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ACCEPT_CONTENT=['json']
CELERY_TASK_SERIALIZER='json'
CELERY_RESULT_SERIALIZER='json'
CELERY_TIMEZONE=Africa/Douala

# =======================
# FILE UPLOAD CONFIGURATION
# =======================
# Limites d'upload
MAX_UPLOAD_SIZE=52428800  # 50MB en octets
ALLOWED_EXTENSIONS=pdf,docx,txt,html

# Chemins des fichiers
MEDIA_ROOT=media/
MEDIA_URL=/media/
STATIC_ROOT=staticfiles/
STATIC_URL=/static/
UPLOAD_DIRECTORY=media/documents_bruts/
PROCESSED_DIRECTORY=resultats/
LOG_DIRECTORY=logs/

# =======================
# JWT AUTHENTICATION CONFIGURATION
# =======================
# Configuration JWT pour l'authentification (Phase 2)
JWT_SECRET=votre_secret_jwt_ici
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=900  # 15 minutes en secondes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 jours en secondes
JWT_ISSUER=xcsm-backend
JWT_AUDIENCE=xcsm-clients

# =======================
# SMTP / EMAIL CONFIGURATION
# =======================
# Configuration email (Gmail SMTP recommandé)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_application_gmail  # Mot de passe d'application, pas le mot de passe du compte
DEFAULT_FROM_EMAIL=XCSM Platform <votre_email@gmail.com>
EMAIL_SUBJECT_PREFIX=[XCSM]

# =======================
# FRONTEND INTEGRATION (CORS)
# =======================
# Configuration CORS pour le frontend Next.js
CORS_ALLOW_ALL_ORIGINS=True  # À METTRE À False EN PRODUCTION
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOWED_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOWED_HEADERS=accept,accept-encoding,authorization,content-type,dnt,origin,user-agent,x-csrftoken,x-requested-with,x-api-key
CORS_ALLOW_CREDENTIALS=True
CORS_MAX_AGE=3600
FRONTEND_URL=http://localhost:3000

# =======================
# SECURITY CONFIGURATION
# =======================
# Sécurité des cookies
SESSION_COOKIE_AGE=1209600  # 2 semaines en secondes
SESSION_COOKIE_SECURE=False  # À METTRE À True EN PRODUCTION AVEC HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Protection CSRF
CSRF_COOKIE_SECURE=False  # À METTRE À True EN PRODUCTION
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SAMESITE=Lax
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Headers de sécurité
X_FRAME_OPTIONS=DENY
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True

# =======================
# LOGGING CONFIGURATION
# =======================
# Niveaux de log
LOG_LEVEL_DJANGO=INFO
LOG_LEVEL_XCSM=DEBUG
LOG_LEVEL_DB=WARNING

# Chemins des fichiers de log
LOG_FILE_PATH=logs/xcsm_backend.log
ERROR_LOG_FILE_PATH=logs/xcsm_errors.log
ACCESS_LOG_FILE_PATH=logs/xcsm_access.log

# Rotation des logs
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=10

# =======================
# DOCUMENT PROCESSING CONFIGURATION
# =======================
# Configuration spécifique au traitement de documents
PDF_EXTRACTION_ENGINE=pymupdf  # Options: pymupdf, pdfminer
PDF_MAX_PAGES=1000
PDF_EXTRACT_IMAGES=False
PDF_PRESERVE_LAYOUT=True

DOCX_CONVERTER=mammoth  # Options: mammoth, python-docx
DOCX_PRESERVE_STYLES=True
DOCX_CONVERT_IMAGES=False

GRANULE_MIN_LENGTH=50  # Caractères minimum par granule
GRANULE_MAX_LENGTH=2000  # Caractères maximum par granule
GRANULE_SEPARATOR_PATTERNS=\n\n,\r\n\r\n,<br/>,<p>
TITLE_DETECTION_THRESHOLD=0.7  # Seuil de confiance pour la détection de titres

# =======================
# API CONFIGURATION
# =======================
# Configuration générale de l'API
API_VERSION=v1
API_BASE_PATH=api/

# Rate limiting
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_BURST=10

# Pagination
PAGE_SIZE_DEFAULT=20
PAGE_SIZE_MAX=100

# =======================
# NOTIFICATIONS CONFIGURATION
# =======================
# Configuration des notifications
NOTIFY_ON_DOCUMENT_PROCESSED=True
NOTIFY_ON_ERROR=True
NOTIFY_ON_SYSTEM_ALERT=True

# Firebase pour notifications push (optionnel)
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json

# =======================
# MONITORING AND METRICS
# =======================
# Monitoring et métriques
ENABLE_METRICS=True
ENABLE_HEALTH_CHECKS=True
PROMETHEUS_METRICS_PATH=/metrics

# =======================
# BACKUP CONFIGURATION
# =======================
# Configuration des sauvegardes automatiques
ENABLE_AUTO_BACKUP=False  # Désactivé en développement
BACKUP_SCHEDULE=0 2 * * *  # Tous les jours à 2h du matin (cron format)
BACKUP_RETENTION_DAYS=7
BACKUP_DIRECTORY=backups/
BACKUP_MYSQL=True
BACKUP_MONGODB=True

# =======================
# DEVELOPMENT SETTINGS
# =======================
# Paramètres spécifiques au développement
ENABLE_DEBUG_TOOLBAR=True
ENABLE_SQL_LOGGING=True
ENABLE_PROFILING=False
CREATE_TEST_DATA=True
TEST_DOCUMENTS_COUNT=3
TEST_USERS_COUNT=5

# =======================
# SCRIPT CONFIGURATION
# =======================
# Configuration pour le script setup-local-env.sh
AUTO_CREATE_SUPERUSER=True
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@xcsm.local
SUPERUSER_PASSWORD=admin123xcsm
AUTO_CREATE_TEST_DATA=True
```

## 📋 Fichier `requirements.txt` Final

```txt
# ============================================
# XCSM BACKEND - DEPENDANCES COMPLÈTES
# ============================================

# CORE DJANGO & REST API
asgiref==3.10.0
Django==5.2.8
djangorestframework==3.16.1
django-cors-headers==4.9.0

# DATABASES
mysqlclient==2.2.7
pymongo==4.15.4
sqlparse==0.5.3
redis==5.2.1

# DOCUMENT PROCESSING (Cœur de XCSM)
PyMuPDF==1.26.6
mammoth==1.11.0
beautifulsoup4==4.12.3
lxml==5.3.1
pillow==12.0.0
dnspython==2.8.0

# ASYNC TASKS & QUEUING
celery==5.4.0

# API DOCUMENTATION & TOOLS
drf-yasg==1.21.7
python-dotenv==1.0.1
django-filter==24.3

# ADMIN & UTILITIES
django-import-export==4.3.14

# AUTHENTICATION (Phase 2 préparation)
djangorestframework-simplejwt==5.4.0

# EMAIL & NOTIFICATIONS
django-templated-mail==1.1.1
django-post-office==3.9.0

# TESTING & QUALITY
pytest==8.3.4
pytest-django==4.9.0
coverage==7.6.7

# PRODUCTION READY
gunicorn==21.2.0
whitenoise==6.9.0

# INTERNATIONALIZATION
tzdata==2025.2

# DEV EXPERIENCE & PRODUCTIVITÉ
django-extensions==3.2.3
ipython==8.30.0

# SÉCURITÉ API
django-ratelimit==4.1.0

# OBSERVABILITÉ & MONITORING
sentry-sdk==2.19.2
```

## 🔄 Workflow d'Initialisation

1. **Cloner le projet** : `git clone https://github.com/PafeDilane/XCSM_Backend.git`
2. **Configurer l'environnement** : `cp .env.example .env` puis éditer les valeurs
3. **Installer les dépendances** : `pip install -r requirements.txt`
4. **Configurer les bases de données** (MySQL, MongoDB, Redis)
5. **Appliquer les migrations** : `python manage.py migrate`
6. **Créer le superutilisateur** : `python manage.py createsuperuser`
7. **Collecter les fichiers statiques** : `python manage.py collectstatic`
8. **Démarrer les services** :
    - Redis : `redis-server`
    - Celery : `celery -A xcsm_project worker --loglevel=info`
    - Django : `python manage.py runserver`

Cette structure garantit une séparation claire des responsabilités et facilite la maintenance et l'évolution du projet.