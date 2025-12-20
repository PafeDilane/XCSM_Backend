<<<<<<< HEAD
# XCSM_Backend
Backend de L'application XCSM en Django


XCSM Backend - Plateforme de Structuration Pédagogique Automatisée

À propos du projet :
XCSM (eXtraction et Structuration de Contenus Multimédia) est une plateforme web d'envergure nationale dédiée à l'extraction et à la structuration automatisée de contenus pédagogiques à partir de documents PDF et DOCX.

Vision :
Révolutionner la gestion des ressources pédagogiques en permettant aux enseignants de déposer des documents (PDF, DOCX, TXT) et d'obtenir automatiquement un cours structuré en sections navigables appelées granules.

Public cible :
Enseignants : Déposer des documents et générer automatiquement des cours structurés
Étudiants : Consulter des contenus organisés et facilement navigables
Administrateurs : Gérer la plateforme et les utilisateurs


✅ Ce qui a été fait (Phase 1 - Fondations)

1. Architecture Django complète
✅ Projet Django initialisé

Framework Django 5.2.8
Django REST Framework pour l'API
CORS configuré pour Next.js
Documentation Swagger intégrée (drf-yasg)

2. Modèles de données (MySQL)
✅ Gestion des utilisateurs

python
- Utilisateur (modèle personnalisé héritant d'AbstractUser)
- Enseignant (profil avec spécialité et département)
- Étudiant (profil avec matricule, niveau, filière)
- Administrateur (profil avec rôle et permissions)

✅ Hiérarchie pédagogique complète

Cours → Partie → Chapitre → Section → SousSection → Granule
Chaque niveau avec UUID, titre, numéro d'ordre
Relations optimisées avec related_name

✅ Gestion des fichiers

python
  FichierSource:
-Métadonnées (titre, date_upload, enseignant)
-Fichier original stocké sur disque
-Référence MongoDB (mongo_transforme_id)
-Statut de traitement (EN_ATTENTE, TRAITE, ERREUR)


1) Traitement automatique des documents
✅ Extraction intelligente

Pour les PDF (PyMuPDF) :

Extraction du texte page par page
Détection automatique des titres (MAJUSCULES, numérotation romaine)
Découpage en blocs de contenu
Pour les DOCX (Mammoth) :

Conversion avec mapping des styles Word
Préservation de la hiérarchie (Heading 1, 2, 3)
Extraction des paragraphes et listes


✅ Génération de structure JSON

json
{
  "metadata": {
    "extraction_date": "2025-12-20T10:30:00",
    "version": "2.0-JSON"
  },
  "sections": [
    {
      "type": "h1",
      "level": 1,
      "content": "Chapitre 1 : Introduction",
      "html": "<h1>Chapitre 1 : Introduction</h1>",
      "children": [
        {
          "type": "granule",
          "level": 4,
          "content": "Python est un langage..."
=======
# XCSM Backend - API de Traitement et Structuration de Contenus Pédagogiques

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-Academic-orange.svg)](LICENSE)

---

##  Table des Matières

1. [Description](#-description)
2. [Objectifs](#-objectifs)
3. [Technologies](#-technologies)
4. [Architecture](#-architecture)
5. [Installation](#-installation)
6. [Configuration](#-configuration)
7. [Utilisation](#-utilisation)
8. [Système de Notifications](#-système-de-notifications)
9. [Tests et Qualité](#-tests-et-qualité)
10. [Déploiement](#-déploiement)
11. [Contribution](#-contribution)
12. [Auteurs](#-auteurs)

---

##  Description

**XCSM Backend** (eXtended Content Structured Module) est une API REST développée avec Django qui transforme des documents pédagogiques volumineux et non structurés (PDF, DOCX, TXT, HTML) en **granules d'apprentissage** exploitables et organisés hiérarchiquement.

### Qu'est-ce qu'un Granule ?

Un **granule** représente une unité d'information pédagogique autonome et significative extraite d'un document source. Au lieu de parcourir un cours d'algorithmique de 200 pages pour trouver la section sur "les arbres binaires", le système découpe automatiquement ce cours en granules logiques.

**Exemple de granulation** :
```
Cours Algorithmique (200 pages)
├── Partie I : Fondamentaux
│   ├── Chapitre 1 : Complexité algorithmique
│   │   ├── Granule 1.1 : Notation Big O
│   │   └── Granule 1.2 : Classes de complexité
│   └── Chapitre 2 : Récursivité
│       ├── Granule 2.1 : Principe de récursivité
│       └── Granule 2.2 : Récursivité terminale
└── Partie II : Structures de Données
    └── Chapitre 3 : Arbres
        ├── Granule 3.1 : Arbres binaires
        └── Granule 3.2 : Arbres AVL
```

### Fonctions Essentielles

1. **Ingestion intelligente** : Réception et validation des documents
2. **Traitement et extraction** : Analyse avec préservation de la structure sémantique
3. **Structuration et stockage** : Organisation hiérarchique avec métadonnées enrichies

---

##  Objectifs

### Objectifs Principaux

- **Automatiser l'extraction** : Transformer des documents bruts en structures exploitables
- **Structurer l'information** : Organiser selon une hiérarchie logique (Partie → Chapitre → Section → Granule)
- **Faciliter l'accès** : Navigation intuitive et recherche ciblée
- **Optimiser l'apprentissage** : Réduire la charge cognitive par unités cohérentes

### Objectifs Techniques

| Critère | Cible |
|---------|-------|
| **Performance** | Documents ≤50 Mo traités en <30s |
| **Précision** | ≥95% d'exactitude dans l'extraction |
| **Interopérabilité** | API REST standardisée |
| **Évolutivité** | Architecture modulaire |
| **Fiabilité** | Gestion robuste des erreurs |

---

##  Technologies

### Stack Backend

| Technologie | Version | Rôle |
|------------|---------|------|
| **Python** | 3.11+ | Langage principal |
| **Django** | 4.2+ | Framework web MVC |
| **Django REST Framework** | 3.14+ | Construction API REST |
| **MySQL** | 8.0+ | Base de données relationnelle (métadonnées) |
| **MongoDB** | 6.0+ | Base NoSQL (stockage granules) |
| **Redis** | 7.0+ | Cache et broker Celery |
| **Celery** | 5.3+ | Tâches asynchrones |

### Bibliothèques de Traitement

| Bibliothèque | Usage |
|--------------|-------|
| **PyMuPDF (fitz)** | Extraction PDF haute performance |
| **python-docx** | Manipulation fichiers DOCX |
| **BeautifulSoup4** | Parser HTML/XML |
| **chardet** | Détection encodage fichiers texte |

### Services Externes

| Service | Usage |
|---------|-------|
| **SendGrid / Mailgun** | Envoi emails transactionnels |
| **Firebase Cloud Messaging** | Notifications push mobile |
| **Web Push Protocol** | Notifications navigateur |

---

##  Architecture

### Structure du Projet

```
xcsm_backend/
├── manage.py                    # Point d'entrée Django CLI
├── requirements.txt             # Dépendances Python
├── README.md                    # Documentation (ce fichier)
├── .gitignore                   # Fichiers exclus versioning
├── .env.example                 # Template variables d'environnement
│
├── env/                         # Environnement virtuel Python
│
├── media/                       # Stockage fichiers uploadés
│   ├── documents_bruts/         # Documents originaux
│   └── photos_profil/           # Images profil utilisateurs
│
├── xcsm_project/                # Configuration globale Django
│   ├── __init__.py
│   ├── settings.py              # Paramètres projet
│   ├── urls.py                  # Routage URL principal
│   ├── wsgi.py                  # Interface WSGI
│   └── asgi.py                  # Interface ASGI
│
└── xcsm/                        # Application principale
    ├── migrations/              # Historique modifications BDD
    ├── models.py                # Modèles de données (ORM)
    ├── views.py                 # Contrôleurs API
    ├── serializers.py           # Transformation données ↔ JSON
    ├── urls.py                  # Routes API application
    ├── permissions.py           # Règles d'autorisation
    ├── processing.py            # Moteur traitement documents
    ├── utils.py                 # Fonctions utilitaires
    ├── admin.py                 # Interface administration
    ├── apps.py                  # Configuration application
    ├── tests.py                 # Tests unitaires
    │
    └── notifications/           # Module notifications
        ├── models.py            # Modèles notifications
        ├── views.py             # API notifications
        ├── services.py          # Logique métier
        ├── tasks.py             # Tâches Celery
        ├── email_templates/     # Templates emails
        └── push/                # Services push
```

### Principes Architecturaux

**Séparation des Couches** (Clean Architecture)
```
┌─────────────────────────────────────┐
│   Views (HTTP/API Layer)            │
├─────────────────────────────────────┤
│   Services (Business Logic)         │
├─────────────────────────────────────┤
│   Repositories (Data Access)        │
├─────────────────────────────────────┤
│   Models (Domain Entities)          │
└─────────────────────────────────────┘
```

**Principes SOLID Appliqués**
- **S**ingle Responsibility : Une classe = une responsabilité
- **O**pen/Closed : Extension sans modification
- **L**iskov Substitution : Substitution types dérivés
- **I**nterface Segregation : Interfaces spécifiques
- **D**ependency Inversion : Dépendance vers abstractions

---

##  Installation

### Prérequis Système

- **Python 3.11+** : `python --version`
- **pip** : Gestionnaire paquets Python
- **MySQL 8.0+** : Base de données relationnelle (métadonnées)
- **MongoDB 6.0+** : Base de données NoSQL (granules)
- **Git** : Contrôle de version
- **Redis 7.0+** (optionnel) : Cache et broker Celery

### Installation Standard

#### 1. Clonage du Dépôt

```bash
git clone https://github.com/PafeDilane/XCSM_Backend.git
cd XCSM_Backend
```

#### 2. Environnement Virtuel

```bash
# Linux/macOS
python3 -m venv env
source env/bin/activate

# Windows
python -m venv env
env\Scripts\activate
```

#### 3. Installation Dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configuration Base de Données

**Option A : SQLite + Stockage Fichiers (Développement)**

Configuration par défaut pour MySQL, granules stockés en fichiers texte dans `resultats/`.

**Option B : MySQL + MongoDB (Production Recommandée)**

**MySQL (Métadonnées)** :
```sql
CREATE DATABASE xcsm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'xcsm_user'@'localhost' IDENTIFIED BY 'mot_de_passe_securise';
GRANT ALL PRIVILEGES ON xcsm_db.* TO 'xcsm_user'@'localhost';
FLUSH PRIVILEGES;
```

**MongoDB (Granules)** :
```bash
# Installation MongoDB
# Ubuntu/Debian
sudo apt-get install -y mongodb-org

# macOS
brew tap mongodb/brew
brew install mongodb-community@6.0

# Démarrage service
sudo systemctl start mongod
sudo systemctl enable mongod

# Vérification
mongosh --eval "db.version()"
```

Configuration connexion MongoDB :
```javascript
// Test de connexion
mongosh
use xcsm_granules
db.createCollection("granules")
db.granules.createIndex({ "document_id": 1, "identifiant": 1 })
```

#### 5. Variables d'Environnement

Créez `.env` à la racine :

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

Contenu `.env` :
```bash
# Django
SECRET_KEY=votre_cle_secrete_django_50_caracteres_minimum
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données MySQL (métadonnées)
DB_ENGINE=mysql
DB_NAME=xcsm_db
DB_USER=xcsm_user
DB_PASSWORD=mot_de_passe_securise
DB_HOST=localhost
DB_PORT=3306

# MongoDB (granules)
MONGO_URI=mongodb://localhost:27017/xcsm_granules
MONGO_DB_NAME=xcsm_granules

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=votre_cle_api_sendgrid
DEFAULT_FROM_EMAIL=XCSM Platform <noreply@xcsm.edu>

# Firebase (notifications mobile)
FIREBASE_CREDENTIALS_PATH=/chemin/vers/firebase-credentials.json

# Frontend
FRONTEND_URL=http://localhost:3000
```

#### 6. Migrations Base de Données

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 7. Création Superutilisateur

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@xcsm.local
# Password: ********
```

#### 8. Collecte Fichiers Statiques

```bash
python manage.py collectstatic --noinput
```

#### 9. Démarrage Serveur

```bash
python manage.py runserver
# Serveur : http://127.0.0.1:8000/
```

**Vérifications** :
- API Root : http://127.0.0.1:8000/api/
- Admin Django : http://127.0.0.1:8000/admin/

---

##  Configuration

### Configuration Celery (Tâches Asynchrones)

**Terminal 1 : Redis**
```bash
redis-server
```

**Terminal 2 : Worker Celery**
```bash
celery -A xcsm_project worker --loglevel=info
```

**Terminal 3 : Celery Beat (tâches périodiques)**
```bash
celery -A xcsm_project beat --loglevel=info
```

**Terminal 4 : Serveur Django**
```bash
python manage.py runserver
```

### Configuration CORS

Pour autoriser requêtes depuis le frontend Next.js :

**xcsm_project/settings.py** :
```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

# Développement
CORS_ALLOW_ALL_ORIGINS = True

# Production (à préférer)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://xcsm-frontend.vercel.app',
]
```

### Configuration Logging

**xcsm_project/settings.py** :
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'xcsm_backend.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'xcsm': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

##  Utilisation

### Endpoints API Principaux

#### Authentification

**Obtention Token JWT**

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "enseignant@xcsm.local",
  "password": "mon_mot_de_passe"
}
```

**Réponse** :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "enseignant",
    "role": "ENSEIGNANT"
  }
}
```

**Utilisation Token** :
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Upload Document

```http
POST /api/upload/
Authorization: Bearer <token>
Content-Type: multipart/form-data

fichier: <binary_file_data>
titre: "Cours d'Algorithmique Avancée"
description: "Support cours 4ème année"
tags: "algorithmique,structures-donnees,python"
```

**Réponse** :
```json
{
  "id": 42,
  "titre": "Cours d'Algorithmique Avancée",
  "type_fichier": "PDF",
  "taille": 5242880,
  "statut_traitement": "EN_ATTENTE",
  "date_upload": "2025-12-18T14:15:00Z",
  "url_fichier": "http://127.0.0.1:8000/media/documents_bruts/..."
}
```

#### Consultation Traitement

```http
GET /api/documents/42/
Authorization: Bearer <token>
```

**Réponse (en cours)** :
```json
{
  "id": 42,
  "titre": "Cours d'Algorithmique Avancée",
  "statut_traitement": "EN_COURS",
  "progression": 67,
  "etape_actuelle": "Segmentation en granules"
}
```

**Réponse (terminé)** :
```json
{
  "id": 42,
  "statut_traitement": "TERMINE",
  "nombre_granules": 127,
  "date_fin_traitement": "2025-12-18T14:23:15Z",
  "url_granules": "/api/granules/?document=42"
}
```

#### Récupération Granules

**Tous les granules d'un document** :
```http
GET /api/granules/?document=42
Authorization: Bearer <token>
```

**Réponse** :
```json
{
  "count": 127,
  "results": [
    {
      "id": 1,
      "identifiant": "1",
      "titre": "Introduction à l'Algorithmique",
      "contenu": "L'algorithmique est la science...",
      "niveau_hierarchie": 1,
      "ordre": 1,
      "parent": null,
      "enfants": [
        {
          "id": 2,
          "identifiant": "1.1",
          "titre": "Définition d'un algorithme",
          "niveau_hierarchie": 2,
          "ordre": 1,
          "enfants": [...]
>>>>>>> 9238fb704d65b36db2dbaa18eda890ad49887380
        }
      ]
    }
  ]
}
<<<<<<< HEAD
✅ Découpage en granules

Découpage ligne par ligne pour granularité maximale
Création automatique de la hiérarchie (Cours/Chapitres/Sections)
Stockage des métadonnées dans MySQL
Stockage du contenu JSON dans MongoDB

1. Bases de données hybrides
✅ MySQL (xcsm_db)

Tables créées :
- xcsm_utilisateur (utilisateurs)
- xcsm_enseignant (profils enseignants)
- xcsm_etudiant (profils étudiants)
- xcsm_administrateur (profils admins)
- xcsm_fichiersource (fichiers uploadés)
- xcsm_cours (cours générés)
- xcsm_partie (parties de cours)
- xcsm_chapitre (chapitres)
- xcsm_section (sections)
- xcsm_soussection (sous-sections)
- xcsm_granule (granules - métadonnées uniquement)
✅ MongoDB (xcsm_granules_db)

Collections créées :
-fichiers_uploades : Structure JSON complète du document
-granules : Contenu atomique de chaque granule

1. API REST fonctionnelle
✅ Endpoints implémentés

Méthode	Endpoint	Description

POST	/api/v1/documents/upload/	Upload et traitement automatique
GET	/api/v1/documents/{id}/json/	Récupérer structure JSON
GET	/api/v1/granules/{id}/	Détail d'un granule
GET	/api/v1/granules/search/?q=terme	Recherche textuelle
GET	/api/v1/cours/{id}/export-json/	Export complet d'un cours
GET	/api/v1/statistics/mongodb/	Statistiques système
✅ Documentation Swagger

Interface interactive : http://localhost:8000/swagger/
Tester tous les endpoints en direct
Exemples de requêtes/réponses

6. Interface d'administration
✅ Admin Django personnalisé

Gestion des utilisateurs et profils
Visualisation des fichiers uploadés
Aperçu de la structure JSON MongoDB
Compteurs de relations (parties, chapitres, granules)
Badges colorés pour les statuts

7. Tests et validation
✅ Suite de tests

Tests unitaires (conversion JSON, découpage)
Tests d'intégration (MySQL + MongoDB)
Script de validation automatique (scripts/test_json_processing.py)
🛠 Technologies utilisées
Backend
Python 3.12 : Langage de programmation
Django 5.2.8 : Framework web
Django REST Framework : Création d'API REST
drf-yasg : Documentation Swagger automatique
django-cors-headers : Gestion CORS pour Next.js
Traitement de documents
PyMuPDF (fitz) : Extraction et parsing PDF
mammoth : Conversion DOCX → HTML sémantique
BeautifulSoup4 : Parsing et nettoyage HTML
Regex (re) : Détection de patterns (titres, numérotation)
Bases de données
MySQL 8.0 : Données structurées (utilisateurs, cours, hiérarchie)
MongoDB 7.0 : Contenus JSON (documents transformés, granules)
PyMongo : Driver MongoDB pour Python
mysqlclient : Driver MySQL pour Django
Outils
VS Code : IDE de développement
MySQL Workbench : Gestion base MySQL
MongoDB Compass : Visualisation MongoDB
Swagger : Tests API


🚀 Ce qu'on peut faire actuellement
Workflow complet fonctionnel
1️⃣ Upload d'un document
Enseignant → Upload PDF/DOCX via Swagger
            ↓
API POST /api/v1/documents/upload/

2️⃣ Traitement automatique
Backend extrait le contenu
     ↓
Détecte les titres (H1, H2, H3)
     ↓
Découpe en granules ligne par ligne
     ↓
Génère la structure JSON

3️⃣ Stockage hybride
MySQL : Métadonnées + Hiérarchie
MongoDB : JSON complet + Granules

4️⃣ Consultation
GET /api/v1/documents/{id}/json/
     ↓
Récupération structure complète
     ↓
Frontend peut afficher le cours
Exemple de résultat
Document uploadé : Introduction_Python.pdf (25 pages)

Résultat obtenu :

✅ Traitement en 3.8 secondes
✅ Cours généré : C-A1B2C3
✅ 7 chapitres détectés automatiquement
✅ 23 sections créées
✅ 189 granules extraits

Stockage :
-MySQL : 1 cours, 7 chapitres, 23 sections, 189 refs granules
-MongoDB : 1 document JSON complet + 189 granules

Visualisation :

MySQL Workbench : Voir tables et relations
MongoDB Compass : Voir JSON complet dans fichiers_uploades
Admin Django : Interface graphique avec aperçus
Swagger : Tester API et voir réponses JSON
📦 Installation
Prérequis
bash
Python 3.12+
MySQL 8.0+
MongoDB 7.0+
1. Cloner le projet
bash
git clone <url-du-repo>
cd XCSM_Backend
2. Environnement virtuel
bash
python -m venv env
source env/bin/activate  # Linux/Mac
env\Scripts\activate     # Windows
3. Installer les dépendances
bash
pip install -r requirements.txt
3. Configurer MySQL
sql
CREATE DATABASE xcsm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
Modifier xcsm_project/settings.py avec vos identifiants MySQL.

5. Lancer MongoDB
bash
mongod  # Démarrer MongoDB en local
6. Migrations Django
bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
7. Lancer le serveur
bash
python manage.py runserver
URLs :

Admin : http://localhost:8000/admin/
Swagger : http://localhost:8000/swagger/
🧪 Tester le système
Test rapide avec le script
bash
python scripts/test_json_processing.py
Ce script va :

Créer un utilisateur test
Uploader un document de test
Vérifier le traitement
Afficher les statistiques
Exporter un JSON de démonstration
Test via Swagger
Ouvrir http://localhost:8000/swagger/
Endpoint : POST /api/v1/documents/upload/
Cliquer "Try it out"
Remplir :
titre : "Mon cours de test"
fichier_original : Sélectionner un PDF/DOCX
Exécuter et voir la réponse
Vérifier les résultats
MySQL Workbench :

sql
SELECT code, titre FROM xcsm_cours ORDER BY date_creation DESC;
SELECT COUNT(*) FROM xcsm_granule;
MongoDB Compass :

Base : xcsm_granules_db
Collection : fichiers_uploades
Voir le champ structure_json → JSON complet visible !
Admin Django :

http://localhost:8000/admin/xcsm/fichiersource/
Cliquer sur un fichier traité
Voir "Aperçu Structure JSON"
📊 Exemple de données
Structure JSON dans MongoDB
json
{
  "fichier_source_id": "abc-123",
  "titre": "Introduction à Python",
  "type_original": "PDF",
  "structure_json": {
    "metadata": {
      "extraction_date": "2025-12-20T10:30:00",
      "version": "2.0-JSON"
    },
    "sections": [
      {
        "type": "h1",
        "level": 1,
        "content": "Chapitre 1 : Les Variables",
        "children": [
          {
            "type": "h2",
            "level": 2,
            "content": "1.1 Types de données",
            "children": [
              {
                "type": "granule",
                "level": 4,
                "content": "Python supporte plusieurs types de données primitifs..."
              }
            ]
          }
        ]
      }
    ]
  }
}
Hiérarchie dans MySQL
Cours : "Introduction à Python" (C-ABC123)
  └─ Partie : "Contenu Principal"
      ├─ Chapitre 1 : "Les Variables"
      │   ├─ Section 1.1 : "Types de données"
      │   │   └─ SousSection : "Contenu"
      │   │       ├─ Granule 1 : "Python supporte plusieurs types..."
      │   │       ├─ Granule 2 : "Les entiers (int) représentent..."
      │   │       └─ Granule 3 : "Les flottants (float) sont..."
      │   └─ Section 1.2 : "Déclaration de variables"
      └─ Chapitre 2 : "Les Structures de Contrôle"
🔗 Pour l'équipe Frontend (Next.js)
Endpoints disponibles
Le backend expose une API REST complète. Exemples d'utilisation :

Upload d'un document
javascript
const formData = new FormData();
formData.append('titre', 'Introduction à Python');
formData.append('fichier_original', file);

const response = await fetch('http://localhost:8000/api/v1/documents/upload/', {
  method: 'POST',
  body: formData
});

const data = await response.json();
// data.id → UUID du fichier
// data.statut_traitement → "TRAITE"
// data.mongo_transforme_id → ID MongoDB
Récupérer la structure d'un cours
javascript
const response = await fetch(`http://localhost:8000/api/v1/documents/${fichierId}/json/`);
const data = await response.json();

// data.json_structure.sections → Array des chapitres/granules
// Utiliser pour construire la navigation
Rechercher dans les granules
javascript
const response = await fetch(`http://localhost:8000/api/v1/granules/search/?q=variable`);
const data = await response.json();

// data.results → Array des granules correspondants
Format des données
Les réponses sont en JSON structuré prêt pour React :

typescript
interface Section {
  type: 'h1' | 'h2' | 'granule';
  level: number;
  content: string;
  html: string;
  children?: Section[];
}
CORS configuré
Le backend accepte les requêtes depuis localhost:3000 (Next.js dev).

Ce qu'il reste à faire

Phase 2 : Fonctionnalités essentielles (En cours)
Authentification complète
 Système JWT/OAuth
 Endpoints login/logout/refresh
 Middleware de permissions
 Protection des routes

Gestion des documents
 Endpoint : Liste des documents d'un enseignant
 Endpoint : Suppression de document
 Endpoint : Modification des métadonnées
 Historique des uploads

Consultation étudiants
 Endpoint : Liste des cours disponibles
 Endpoint : Contenu d'un cours avec hiérarchie
 Endpoint : Navigation entre granules
 Filtrage par niveau/filière

Phase 3 : Fonctionnalités avancées
Recherche et filtrage
 Recherche full-text optimisée (index MongoDB)
 Filtres par tags/catégories
 Tri par pertinence
 Historique de recherche

Édition de contenus
 Endpoint : Modifier un granule
 Endpoint : Réorganiser les sections
 Endpoint : Fusionner/diviser des granules
 Validation par l'enseignant

Génération de documents
 Export cours en PDF
 Export cours en DOCX
 Sélection de granules pour générer un document
 Templates prédéfinis

Génération d'exercices (IA)
 Génération QCM depuis granules
 Génération exercices à trous
 Questions Vrai/Faux
 Validation enseignant

Phase 4 : Déploiement et optimisation
Production
 Configuration pour serveur de production
 Gestion des variables d'environnement
 HTTPS et certificats SSL
 Configuration Nginx/Apache

Performance
 Cache Redis
 Optimisation requêtes MySQL
 Index MongoDB
 Compression des réponses API

Monitoring
 Logs centralisés
 Alertes erreurs
 Métriques de performance
 Tableau de bord admin
📈 Statistiques actuelles
Capacités testées :

✅ Documents PDF jusqu'à 50 Mo
✅ Documents DOCX jusqu'à 20 Mo
✅ Traitement en moyenne 2-5 secondes par document
✅ Extraction de 100-200 granules par document moyen
✅ Stockage hybride MySQL + MongoDB fonctionnel
Tests effectués :

✅ 15+ documents PDF traités avec succès
✅ 8+ documents DOCX traités avec succès
✅ Détection automatique de titres : ~85% précision
✅ Découpage en granules : 100% fonctionnel
Équipe Backend
Architecte Backend : [Dilane PAFE, TCHAPET Rolain, NJANJA Brusly, MANFOUO Braun]

Support important
Documentation
Swagger : http://localhost:8000/swagger/
Admin Django : http://localhost:8000/admin/
Fichier : MIGRATION_JSON.md (détails techniques)
Problèmes courants
"Connection refused MongoDB"

bash
sudo systemctl start mongod  # Linux
brew services start mongodb-community  # macOS
"Access denied MySQL"

bash
# Vérifier les identifiants dans settings.py
# Créer l'utilisateur si nécessaire
"Module not found"

bash
pip install -r requirements.txt
Contact
Pour toute question, créer une issue sur GitHub ou contacter l'équipe backend.

Licence
Ce projet est développé dans le cadre d'un projet académique d'envergure nationale.

État actuel
┌────────────────────────────────────────┐
│    BACKEND XCSM - OPÉRATIONNEL      │
│                                        │
│    Phase 1 : 100% (Fondations)      │
│    Phase 2 : 30% (En cours)         │
│    Phase 3 : 0% (Planifiée)         │
│    Phase 4 : 0% (Planifiée)         │
│                                        │
│   Le cœur du système fonctionne !   │
└────────────────────────────────────────┘
Apres les modification precedente, Le backend sera prêt pour l'intégration avec le frontend Next.js !


=======
```

**Recherche textuelle** :
```http
GET /api/granules/?search=arbres+binaires
Authorization: Bearer <token>
```

**Filtrage par niveau** :
```http
GET /api/granules/?document=42&niveau_hierarchie=2
Authorization: Bearer <token>
```

#### Modification Granule

```http
PATCH /api/granules/78/
Authorization: Bearer <token>
Content-Type: application/json

{
  "contenu": "Un arbre binaire est...[texte enrichi]",
  "tags": ["structures-donnees", "arbres", "recursion"]
}
```

#### Suppression Document

```http
DELETE /api/documents/42/
Authorization: Bearer <token>
```

### Intégration Frontend

**Exemple avec Axios (Next.js)** :

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Upload document
export const uploadDocument = async (file: File, titre: string) => {
  const formData = new FormData();
  formData.append('fichier', file);
  formData.append('titre', titre);
  
  return api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Récupération granules
export const getGranules = async (documentId: number) => {
  return api.get(`/granules/?document=${documentId}`);
};
```

---

##  Système de Notifications

Le système de notifications permet d'informer les utilisateurs en temps réel des événements importants via plusieurs canaux.

### Canaux de Notification

| Canal | Description | Usage |
|-------|-------------|-------|
| **In-App** | Notifications internes plateforme | Historique permanent |
| **Email** | Emails transactionnels | Événements détaillés |
| **Push** | Notifications appareil | Alertes urgentes |

### Types de Notifications

- `DOCUMENT_TRAITE` : Document traité avec succès
- `DOCUMENT_ERREUR` : Erreur traitement document
- `NOUVELLE_EVALUATION` : Évaluation publiée
- `EVALUATION_CORRIGEE` : Correction disponible
- `NOUVEAU_MESSAGE` : Nouveau message discussion
- `SYSTEME` : Notifications système

### Configuration Notifications

#### Installation Dépendances

```bash
pip install django-templated-mail celery-email firebase-admin pywebpush
```

#### Configuration Firebase (Push Mobile)

1. Créer projet Firebase : https://console.firebase.google.com
2. Activer Firebase Cloud Messaging
3. Télécharger fichier credentials JSON
4. Ajouter chemin dans `.env` :

```bash
FIREBASE_CREDENTIALS_PATH=/chemin/vers/firebase-credentials.json
```

#### Configuration Web Push (Navigateur)

Générer clés VAPID :

```bash
python -c "from pywebpush import Vapid; v=Vapid(); v.save_key('.'); print('Clés générées')"
```

Ajouter dans `.env` :
```bash
WEBPUSH_VAPID_PRIVATE_KEY_PATH=/chemin/vers/vapid_private.pem
WEBPUSH_VAPID_PUBLIC_KEY_PATH=/chemin/vers/vapid_public.pem
WEBPUSH_CONTACT_EMAIL=admin@xcsm.edu
```

### Endpoints Notifications

**Récupération notifications utilisateur** :
```http
GET /api/notifications/
Authorization: Bearer <token>
```

**Marquer notification comme lue** :
```http
PATCH /api/notifications/{id}/marquer_lue/
Authorization: Bearer <token>
```

**Enregistrer device token** :
```http
POST /api/notifications/devices/
Authorization: Bearer <token>
Content-Type: application/json

{
  "token": "device_token_fcm_ou_subscription_web",
  "type": "IOS|ANDROID|WEB",
  "nom_device": "iPhone 13"
}
```

**Gestion préférences** :
```http
GET /api/notifications/preferences/
PATCH /api/notifications/preferences/

{
  "activer_emails": true,
  "activer_push": true,
  "activer_in_app": true,
  "ne_pas_deranger_debut": "22:00",
  "ne_pas_deranger_fin": "07:00",
  "preferences_par_type": {
    "DOCUMENT_TRAITE": ["EMAIL", "PUSH"],
    "NOUVELLE_EVALUATION": ["EMAIL", "PUSH", "IN_APP"]
  }
}
```

---

##  Tests et Qualité

### Convention de Nommage

**Variables** : `snake_case`
```python
user_name = "John Doe"
order_date = datetime.now()
total_amount = 100.50
```

**Constantes** : `UPPER_CASE`
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"
```

**Classes** : `PascalCase`
```python
class DocumentProcessor:
    pass

class GranuleService:
    pass
```

**Fonctions/Méthodes** : `snake_case`
```python
def calculate_total():
    pass

def get_user_by_email():
    pass
```

### Tests Unitaires

**Structure des tests** :
```
xcsm/tests/
├── __init__.py
├── test_models.py
├── test_views.py
├── test_services.py
├── test_processing.py
└── test_utils.py
```

**Exemple test** :
```python
# xcsm/tests/test_processing.py
from django.test import TestCase
from xcsm.processing import extract_pdf, segment_content
from xcsm.models import Document


class ProcessingTestCase(TestCase):
    """Tests for document processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.document = Document.objects.create(
            titre="Test Document",
            type_fichier="PDF"
        )
    
    def test_should_extract_text_from_pdf(self):
        """Test PDF text extraction."""
        # Given
        pdf_path = "test_data/sample.pdf"
        
        # When
        extracted_text = extract_pdf(pdf_path)
        
        # Then
        self.assertIsNotNone(extracted_text)
        self.assertGreater(len(extracted_text), 0)
    
    def test_should_return_error_when_file_not_found(self):
        """Test error handling for missing file."""
        # Given
        invalid_path = "nonexistent.pdf"
        
        # When/Then
        with self.assertRaises(FileNotFoundError):
            extract_pdf(invalid_path)
```

**Exécution tests** :
```bash
# Tous les tests
python manage.py test

# Tests spécifiques
python manage.py test xcsm.tests.test_processing

# Avec coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Rapport HTML dans htmlcov/
```

### Outils Qualité

**Configuration flake8** (`.flake8`) :
```ini
[flake8]
max-line-length = 120
exclude = 
    .git,
    __pycache__,
    env,
    migrations,
    settings.py
ignore = E203, W503
```

**Configuration black** (`pyproject.toml`) :
```toml
[tool.black]
line-length = 120
target-version = ['py311']
exclude = '''
/(
    \.git
  | \.venv
  | env
  | migrations
)/
'''
```

**Vérification qualité** :
```bash
# Formatage automatique
black .

# Tri imports
isort .

# Vérification style
flake8

# Analyse statique
pylint xcsm/
```

### Couverture de Tests

**Objectif** : ≥80% de couverture

```bash
# Génération rapport coverage
coverage run --source='xcsm' manage.py test
coverage report

# Résultat attendu
Name                      Stmts   Miss  Cover
---------------------------------------------
xcsm/__init__.py              4      0   100%
xcsm/models.py              156     12    92%
xcsm/views.py               234     23    90%
xcsm/processing.py          312     35    89%
xcsm/services.py            178     18    90%
xcsm/utils.py                89      8    91%
---------------------------------------------
TOTAL                       973     96    90%
```

---

##  Déploiement

### Déploiement Production

#### 1. Préparation

```bash
# Désactiver mode debug
DEBUG=False

# Définir hosts autorisés
ALLOWED_HOSTS=xcsm-api.example.com,www.xcsm-api.example.com

# Générer nouvelle SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 2. Configuration Gunicorn

**Installation** :
```bash
pip install gunicorn
```

**Fichier gunicorn_config.py** :
```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
errorlog = "/var/log/xcsm/gunicorn_error.log"
accesslog = "/var/log/xcsm/gunicorn_access.log"
loglevel = "info"
```

**Démarrage** :
```bash
gunicorn xcsm_project.wsgi:application -c gunicorn_config.py
```

#### 3. Configuration Nginx

**Fichier /etc/nginx/sites-available/xcsm** :
```nginx
upstream xcsm_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name xcsm-api.example.com;
    
    client_max_body_size 50M;
    
    location /static/ {
        alias /var/www/xcsm/static/;
    }
    
    location /media/ {
        alias /var/www/xcsm/media/;
    }
    
    location / {
        proxy_pass http://xcsm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Activation** :
```bash
sudo ln -s /etc/nginx/sites-available/xcsm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Configuration Systemd (Gunicorn)

**Fichier /etc/systemd/system/xcsm.service** :
```ini
[Unit]
Description=XCSM Backend Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/xcsm
Environment="PATH=/var/www/xcsm/env/bin"
ExecStart=/var/www/xcsm/env/bin/gunicorn xcsm_project.wsgi:application -c gunicorn_config.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Activation** :
```bash
sudo systemctl daemon-reload
sudo systemctl start xcsm
sudo systemctl enable xcsm
sudo systemctl status xcsm
```

#### 5. Configuration Celery (Systemd)

**Worker Celery** (/etc/systemd/system/celery.service) :
```ini
[Unit]
Description=Celery Workers
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/xcsm
Environment="PATH=/var/www/xcsm/env/bin"
ExecStart=/var/www/xcsm/env/bin/celery multi start worker \
    -A xcsm_project \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log \
    --loglevel=INFO

[Install]
WantedBy=multi-user.target
```

**Celery Beat** (/etc/systemd/system/celerybeat.service) :
```ini
[Unit]
Description=Celery Beat Scheduler
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/xcsm
Environment="PATH=/var/www/xcsm/env/bin"
ExecStart=/var/www/xcsm/env/bin/celery -A xcsm_project beat \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log \
    --loglevel=INFO

[Install]
WantedBy=multi-user.target
```

### Déploiement Docker

Le déploiement via Docker permet d'encapsuler l'application et ses dépendances dans des conteneurs isolés, garantissant ainsi une portabilité et une reproductibilité optimales entre les environnements de développement, de test et de production.

**Dockerfile** :
```dockerfile
FROM python:3.11-slim

# Définition des variables d'environnement Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Création du répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copie du code source
COPY . .

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "xcsm_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**docker-compose.yml** :
```yaml
version: '3.8'

services:
  # Base de données MySQL pour métadonnées
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    networks:
      - xcsm_network

  # MongoDB pour stockage granules
  mongodb:
    image: mongo:6.0
    environment:
      MONGO_INITDB_DATABASE: xcsm_granules
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"
    networks:
      - xcsm_network

  # Redis pour cache et broker Celery
  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"
    networks:
      - xcsm_network

  # Application Django
  web:
    build: .
    command: gunicorn xcsm_project.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - mongodb
      - redis
    networks:
      - xcsm_network

  # Worker Celery pour tâches asynchrones
  celery_worker:
    build: .
    command: celery -A xcsm_project worker --loglevel=info
    volumes:
      - .:/app
      - media_volume:/app/media
    env_file:
      - .env
    depends_on:
      - db
      - mongodb
      - redis
    networks:
      - xcsm_network

  # Celery Beat pour tâches périodiques
  celery_beat:
    build: .
    command: celery -A xcsm_project beat --loglevel=info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - mongodb
      - redis
    networks:
      - xcsm_network

volumes:
  mysql_data:
  mongo_data:
  static_volume:
  media_volume:

networks:
  xcsm_network:
    driver: bridge
```

**Commandes Docker** :
```bash
# Construction des images
docker-compose build

# Démarrage des services
docker-compose up -d

# Vérification des logs
docker-compose logs -f web

# Exécution des migrations
docker-compose exec web python manage.py migrate

# Création superutilisateur
docker-compose exec web python manage.py createsuperuser

# Arrêt des services
docker-compose down

# Arrêt avec suppression des volumes
docker-compose down -v
```

---

##  Contribution

### Guide de Contribution

Nous encourageons les contributions de la communauté pour améliorer continuellement XCSM. Voici comment vous pouvez participer au développement du projet :

#### 1. Fork et Clone

```bash
# Fork le projet sur GitHub
# Puis clonez votre fork
git clone https://github.com/votre-username/XCSM_Backend.git
cd XCSM_Backend
```

#### 2. Création d'une Branche

Créez une branche pour votre fonctionnalité ou correction :

```bash
# Pour une nouvelle fonctionnalité
git checkout -b feature/nom-fonctionnalite

# Pour une correction de bug
git checkout -b bugfix/description-bug

# Pour un hotfix urgent
git checkout -b hotfix/correction-urgente
```

#### 3. Développement

Respectez les conventions de nommage et les bonnes pratiques décrites dans la charte de développement :

- **Code** : Utilisez `snake_case` pour les fonctions et variables
- **Classes** : Utilisez `PascalCase`
- **Constantes** : Utilisez `UPPER_CASE`
- **Commentaires** : En anglais, clairs et concis
- **Documentation** : Docstrings pour toutes les fonctions publiques

#### 4. Tests

Ajoutez des tests pour toute nouvelle fonctionnalité :

```bash
# Exécuter les tests
python manage.py test

# Avec couverture
coverage run --source='xcsm' manage.py test
coverage report
```

Assurez-vous que la couverture de tests reste ≥80%.

#### 5. Qualité du Code

Vérifiez la qualité du code avant de commiter :

```bash
# Formatage automatique
black .

# Tri des imports
isort .

# Vérification style
flake8

# Analyse statique
pylint xcsm/
```

#### 6. Commits

Écrivez des messages de commit clairs et explicites en anglais :

```bash
# Format recommandé
git commit -m "Add user authentication feature"
git commit -m "Fix PDF parsing for large documents"
git commit -m "Improve granule segmentation algorithm"
```

**Bonnes pratiques de commit** :
- Verbe à l'impératif en début de message
- Description concise en une ligne
- Ajout de détails si nécessaire après une ligne vide

#### 7. Pull Request

Soumettez votre contribution via une Pull Request :

1. Poussez votre branche vers votre fork
```bash
git push origin feature/nom-fonctionnalite
```

2. Créez une Pull Request sur le dépôt principal
3. Décrivez clairement les modifications apportées
4. Référencez les issues associées si applicable
5. Attendez la revue de code

### Standards de Revue de Code

Chaque Pull Request sera évaluée selon les critères suivants :

-  Respect des conventions de nommage
-  Tests unitaires présents et passants
-  Couverture de code ≥80%
-  Documentation à jour
-  Pas de régression fonctionnelle
-  Code propre et lisible
-  Conformité avec les principes SOLID

### Signalement de Bugs

Pour signaler un bug, utilisez le système d'issues GitHub :

1. Vérifiez que le bug n'a pas déjà été signalé
2. Créez une nouvelle issue avec le template "Bug Report"
3. Décrivez le problème de manière détaillée :
   - Environnement (OS, versions Python/Django)
   - Étapes de reproduction
   - Comportement attendu vs observé
   - Logs et messages d'erreur
   - Captures d'écran si pertinent

### Propositions d'Améliorations

Pour proposer une nouvelle fonctionnalité :

1. Créez une issue avec le template "Feature Request"
2. Expliquez le besoin et le cas d'usage
3. Décrivez la solution envisagée
4. Mentionnez les alternatives considérées

---

##  Glossaire

Ce glossaire définit les termes techniques et les concepts clés utilisés dans le projet XCSM, facilitant ainsi la compréhension pour tous les contributeurs et utilisateurs.

### A

**API (Application Programming Interface)** : Interface de programmation qui permet à différentes applications de communiquer entre elles. Dans XCSM, l'API REST permet au frontend Next.js de communiquer avec le backend Django pour échanger des données (upload de documents, récupération de granules, authentification).

**ASGI (Asynchronous Server Gateway Interface)** : Interface serveur asynchrone pour Python, permettant de gérer des connexions longues durée et des opérations asynchrones. Django 4.2+ supporte nativement ASGI pour les fonctionnalités temps réel comme les WebSockets.

**Authentification JWT (JSON Web Token)** : Mécanisme d'authentification basé sur des jetons cryptés qui permettent d'identifier un utilisateur sans avoir à stocker sa session côté serveur. Chaque requête API inclut un token JWT dans son en-tête Authorization.

### B

**Backend** : Partie serveur d'une application web qui gère la logique métier, les accès base de données, et les traitements. Le backend XCSM est développé en Django et expose une API REST consommable par le frontend.

**Broker (Courtier de messages)** : Système intermédiaire qui gère la file d'attente des tâches asynchrones. Redis joue ce rôle dans XCSM pour Celery, stockant temporairement les tâches en attente d'exécution.

### C

**Cache** : Système de stockage temporaire de données fréquemment accédées pour accélérer les performances. Redis sert de cache dans XCSM pour stocker les résultats de parsing récents et éviter des retraitements coûteux.

**Celery** : Framework Python de gestion de tâches asynchrones et distribuées. Dans XCSM, Celery traite les opérations longues comme le parsing de documents volumineux et l'envoi de notifications, sans bloquer les réponses API.

**Celery Beat** : Planificateur de tâches périodiques pour Celery, similaire à un cron système. Il permet d'exécuter automatiquement des tâches à intervalles réguliers (exemple : nettoyage des notifications expirées chaque nuit à 2h).

**Clean Architecture** : Approche de conception logicielle qui sépare clairement les différentes couches d'une application (présentation, logique métier, accès aux données). XCSM suit cette architecture pour garantir maintenabilité et testabilité.

**CORS (Cross-Origin Resource Sharing)** : Mécanisme de sécurité qui autorise ou refuse les requêtes HTTP provenant d'origines différentes. XCSM configure CORS pour permettre au frontend Next.js (localhost:3000) d'accéder à l'API Django (localhost:8000).

**Coverage (Couverture de tests)** : Pourcentage du code source exécuté lors des tests. XCSM vise une couverture ≥80%, garantissant que la majorité du code est testé et validé.

### D

**Django** : Framework web Python de haut niveau suivant le pattern MVT (Model-View-Template). Django fournit un ORM puissant, un système d'authentification intégré, et des outils d'administration pour développer rapidement des applications robustes.

**Django REST Framework (DRF)** : Extension de Django facilitant la création d'APIs REST. DRF fournit des serializers pour transformer les modèles Django en JSON, des viewsets pour gérer les endpoints CRUD, et des systèmes d'authentification/permissions.

**Docstring** : Chaîne de documentation placée au début d'une fonction, classe ou module Python. Les docstrings décrivent le but, les paramètres, les valeurs de retour et les exceptions possibles, facilitant la compréhension et la maintenance du code.

**Docker** : Plateforme de conteneurisation permettant d'empaqueter une application avec toutes ses dépendances dans un conteneur isolé. Docker garantit que XCSM fonctionne de manière identique sur tous les environnements (développement, test, production).

### E

**Endpoint** : Point d'accès d'une API REST correspondant à une URL spécifique. Exemples dans XCSM : `/api/upload/` pour uploader un document, `/api/granules/` pour récupérer les granules.

**Environnement virtuel (venv)** : Environnement Python isolé contenant ses propres paquets et dépendances, évitant les conflits entre projets. XCSM utilise un environnement virtuel dans le dossier `env/`.

### F

**Firebase Cloud Messaging (FCM)** : Service Google d'envoi de notifications push vers des applications mobiles iOS et Android. XCSM utilise FCM pour notifier les utilisateurs sur leurs smartphones des événements importants (document traité, nouvelle évaluation).

**flake8** : Outil Python de vérification de style et de qualité du code, vérifiant la conformité avec les conventions PEP 8. XCSM utilise flake8 avec une limite de 120 caractères par ligne.

**Frontend** : Partie client d'une application web que l'utilisateur voit et avec laquelle il interagit. Le frontend XCSM est développé en Next.js (React) et communique avec le backend via l'API REST.

### G

**Granule** : Unité d'information pédagogique autonome et significative extraite d'un document source. Un granule peut être un chapitre, une section, ou une sous-section, organisé hiérarchiquement pour faciliter la consultation ciblée.

**Gunicorn** : Serveur HTTP Python WSGI pour servir des applications Django en production. Gunicorn gère efficacement plusieurs requêtes simultanées grâce à son architecture multi-workers.

### H

**HTTP (Hypertext Transfer Protocol)** : Protocole de communication utilisé sur le web pour échanger des données entre client et serveur. XCSM utilise HTTP pour son API REST avec les méthodes GET, POST, PATCH, DELETE.

### I

**Indentation** : Espace en début de ligne définissant la structure hiérarchique du code Python. XCSM utilise 4 espaces par niveau d'indentation conformément à PEP 8.

**isort** : Outil Python de tri automatique des imports, les organisant alphabétiquement par sections (bibliothèque standard, paquets tiers, modules locaux). XCSM l'utilise pour maintenir un code organisé.

### J

**JSON (JavaScript Object Notation)** : Format léger d'échange de données lisible par les humains et facilement parsable par les machines. L'API XCSM communique exclusivement en JSON pour les requêtes et réponses.

### L

**Logging** : Système d'enregistrement des événements applicatifs (informations, avertissements, erreurs) pour faciliter le debugging et le monitoring. XCSM configure des logs détaillés dans `xcsm_backend.log`.

**LMS (Learning Management System)** : Plateforme de gestion de l'apprentissage en ligne (exemple : Moodle, Canvas). XCSM peut s'intégrer aux LMS pour enrichir leurs fonctionnalités de gestion de contenu.

### M

**Middleware** : Composant logiciel intercalé entre la requête HTTP et la vue Django, permettant de traiter la requête avant qu'elle n'atteigne la vue. XCSM utilise des middlewares pour la sécurité CSRF, CORS, et l'authentification.

**Migration** : Script généré automatiquement par Django pour modifier le schéma de la base de données (ajout/suppression de tables, modification de colonnes). Les migrations garantissent la cohérence entre les modèles Python et la structure BDD.

**Modèle (Model)** : Classe Python représentant une table de base de données dans l'ORM Django. Chaque attribut du modèle correspond à un champ de la table. Exemples dans XCSM : `Document`, `Granule`, `Notification`.

**MongoDB** : Système de gestion de base de données NoSQL orienté documents. XCSM utilise MongoDB 6.0+ pour stocker les granules d'apprentissage avec leurs structures variables et hiérarchiques, offrant une flexibilité supérieure à une base relationnelle pour ce type de données semi-structurées.

**MySQL** : Système de gestion de base de données relationnelle open source. XCSM utilise MySQL 8.0+ en production pour stocker les métadonnées des documents, les informations utilisateurs, et les relations entre entités.

### N

**Next.js** : Framework React de développement web avec rendu côté serveur (SSR) et génération de sites statiques (SSG). Le frontend XCSM est développé en Next.js 15.1.6 pour des performances optimales.

**Nginx** : Serveur web et reverse proxy haute performance. En production, Nginx distribue les requêtes vers Gunicorn et sert les fichiers statiques de XCSM.

**Notification In-App** : Notification interne à la plateforme XCSM, stockée en base de données et affichée dans l'interface utilisateur. Contrairement aux emails ou push, elle persiste dans l'historique de l'utilisateur.

**NoSQL** : Famille de systèmes de gestion de bases de données non relationnelles, offrant flexibilité et scalabilité pour les données semi-structurées. MongoDB, utilisé dans XCSM pour stocker les granules, est une base NoSQL orientée documents permettant de stocker des structures JSON complexes et hiérarchiques sans schéma rigide.

### O

**ORM (Object-Relational Mapping)** : Technique de programmation qui permet de manipuler des bases de données relationnelles via des objets Python plutôt que du SQL brut. L'ORM Django transforme automatiquement les requêtes Python en SQL.

### P

**Pagination** : Technique de division d'un grand ensemble de résultats en plusieurs pages. L'API XCSM pagine les granules à 20 éléments par page pour optimiser les performances et l'expérience utilisateur.

**Parsing** : Processus d'analyse d'un document pour en extraire la structure et le contenu. Le parseur XCSM utilise PyMuPDF pour extraire le texte des PDF et identifier les sections hiérarchiques.

**PascalCase** : Convention de nommage où chaque mot commence par une majuscule sans séparation. Utilisé dans XCSM pour les noms de classes : `DocumentProcessor`, `GranuleService`.

**PEP 8** : Guide de style officiel pour le code Python, définissant les conventions de nommage, d'indentation, et d'organisation. XCSM respecte strictement PEP 8 avec quelques adaptations (limite 120 caractères).

**Permissions** : Système de contrôle d'accès définissant qui peut effectuer quelles actions sur quelles ressources. Django REST Framework fournit des classes de permissions que XCSM personnalise pour gérer les droits enseignants/étudiants.

**PyMuPDF (fitz)** : Bibliothèque Python haute performance pour la manipulation de fichiers PDF. XCSM l'utilise pour extraire le texte, préserver la structure hiérarchique, et traiter des documents volumineux rapidement.

**pylint** : Outil d'analyse statique du code Python détectant les erreurs, les mauvaises pratiques, et les violations de style. XCSM l'utilise en complément de flake8 pour maintenir une qualité de code élevée.

### R

**React** : Bibliothèque JavaScript pour construire des interfaces utilisateur via des composants réutilisables. Le frontend XCSM utilise React 19.0.0 avec une architecture basée sur les hooks.

**Redis** : Système de stockage de données en mémoire ultra-rapide. XCSM utilise Redis 7.0+ comme cache pour les résultats fréquemment accédés et comme broker pour les tâches Celery.

**REST (Representational State Transfer)** : Style architectural pour les APIs web basé sur HTTP, utilisant les méthodes standard (GET, POST, PUT, DELETE) et les codes de statut. L'API XCSM est entièrement RESTful.

**Retry (Réessai)** : Mécanisme de nouvelle tentative automatique d'une opération échouée. Les tâches Celery d'envoi de notifications dans XCSM réessayent jusqu'à 3 fois avec délai exponentiel en cas d'échec.

### S

**Scalabilité** : Capacité d'un système à gérer une charge croissante en ajoutant des ressources. L'architecture modulaire de XCSM et l'utilisation de Celery garantissent une bonne scalabilité horizontale.

**SCORM (Sharable Content Object Reference Model)** : Standard d'interopérabilité pour les contenus e-learning. XCSM peut exporter les granules au format SCORM pour intégration dans les LMS.

**Segmentation** : Processus de division d'un document en unités logiques (granules). L'algorithme de segmentation XCSM identifie les parties, chapitres, sections via des patterns regex et l'analyse de structure.

**Serializer** : Composant Django REST Framework transformant des instances de modèles en JSON (sérialisation) et vice-versa (désérialisation). XCSM définit des serializers pour Document, Granule, Notification.

**snake_case** : Convention de nommage où les mots sont séparés par des underscores et en minuscules. Utilisé dans XCSM pour les variables et fonctions : `user_name`, `calculate_total()`.

**SOLID** : Ensemble de 5 principes de conception orientée objet (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion). XCSM applique ces principes pour une architecture maintenable.

**SQLite** : Système de gestion de base de données léger intégré. XCSM utilise SQLite par défaut en développement avant de passer à MySQL en production.

**systemd** : Système d'initialisation et gestionnaire de services pour Linux. XCSM utilise systemd pour gérer Gunicorn, Celery Worker, et Celery Beat comme services système en production.

### T

**Tailwind CSS** : Framework CSS utilitaire fournissant des classes prédéfinies pour styliser rapidement les composants. Le frontend XCSM utilise Tailwind CSS 3.4.1 pour un design cohérent et responsive.

**Token JWT** : Jeton d'authentification crypté contenant les informations d'identification de l'utilisateur. Chaque requête API authentifiée de XCSM inclut un token JWT valide dans l'en-tête HTTP.

**TypeScript** : Sur-ensemble de JavaScript ajoutant un typage statique. Le frontend XCSM est développé en TypeScript pour détecter les erreurs dès la compilation et améliorer la maintenabilité.

### U

**UPPER_CASE** : Convention de nommage tout en majuscules avec underscores pour les constantes. Exemples XCSM : `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`, `API_VERSION`.

**UUID (Universally Unique Identifier)** : Identifiant unique universel de 128 bits. XCSM utilise des UUIDs pour nommer les fichiers uploadés, évitant ainsi les collisions de noms.

### V

**VAPID (Voluntary Application Server Identification)** : Protocole d'identification pour l'envoi de notifications Web Push. XCSM génère une paire de clés VAPID pour authentifier les requêtes push vers les navigateurs.

**Virtualenv (Environnement virtuel)** : Voir **Environnement virtuel (venv)**.

**View (Vue)** : Fonction ou classe Django qui reçoit une requête HTTP et retourne une réponse HTTP. Les views XCSM gèrent la logique métier pour l'upload de documents, la récupération de granules, l'authentification.

### W

**Web Push** : Protocole standard W3C permettant d'envoyer des notifications vers les navigateurs web même lorsque le site n'est pas ouvert. XCSM utilise Web Push pour notifier les utilisateurs sur Chrome, Firefox, Safari.

**Webhook** : Mécanisme de notification HTTP permettant à une application d'envoyer des données en temps réel vers une autre application. XCSM peut configurer des webhooks pour notifier des événements (document traité, évaluation publiée).

**Worker** : Processus Celery qui exécute les tâches asynchrones en arrière-plan. XCSM déploie plusieurs workers Celery pour traiter parallèlement le parsing de documents et l'envoi de notifications.

**WSGI (Web Server Gateway Interface)** : Interface standard entre les serveurs web et les applications Python. Gunicorn implémente WSGI pour servir l'application Django XCSM en production.

---

##  Auteurs

**XCSM - Team 4GI Promo 2027**  
École Nationale Supérieure Polytechnique de Yaoundé (ENSP)

### Membres de l'Équipe

- **BrianBrusly**   
- **PafeDilane**  
- **ROLAINTCHAPET** 
- **BraunManfouo** 

### Supervision

**Superviseur** : Pr BATCHAKUI Bernabé  
Département de Génie Informatique  
École Nationale Supérieure Polytechnique de Yaoundé

### Contact & Contributions

- **Email** :  yowyob.4gi.enspy.promo.2027@gmail.com
  *(Pour toute question relative au projet, suggestions d'amélioration, ou demandes de collaboration)*

-  **GitHub** : https://github.com/PafeDilane/XCSM_Backend  
  *(Dépôt officiel du code source, issues, et pull requests)*

-  **Documentation complète** : Voir rapport technique joint  
  *(Rapport détaillé de 39 pages incluant modélisation UML, analyse et conception)*

-  **Site web** : *À venir*  
  *(Plateforme de démonstration et documentation utilisateur)*

### Licence NADA 

**Projet académique à but pédagogique**

Ce projet a été développé dans le cadre du cursus de 4ème année de Génie Informatique à l'ENSP de Yaoundé. Il constitue une contribution significative à l'amélioration de l'apprentissage numérique et de la gestion des contenus pédagogiques.

Le code source est disponible sous licence académique, autorisant l'utilisation à des fins éducatives et de recherche. Pour toute utilisation commerciale ou redistribution, veuillez contacter l'équipe de développement.

---
**Année Académique** : 2025-2026

**Dernière mise à jour** : Décembre 2025
---

> *« Transformer l'abondance informationnelle en parcours d'apprentissage structurés et accessibles »*

---

##  Références et Ressources

### Documentation Officielle

- [Django Documentation](https://docs.djangoproject.com/en/4.2/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)

### Bibliothèques et Outils

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)

### Standards et Bonnes Pratiques

- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [REST API Guidelines](https://restfulapi.net/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### Articles de Recherche

Les références bibliographiques complètes du projet sont disponibles dans le rapport technique, incluant les travaux sur :
- La segmentation automatique de contenus pédagogiques
- La charge cognitive et l'apprentissage numérique
- Les systèmes de gestion de l'apprentissage (LMS)
- L'optimisation de la rétention des connaissances

---

*Merci d'avoir consulté la documentation XCSM Backend. Pour toute question ou contribution, n'hésitez pas à nous contacter via GitHub ou par email.*
>>>>>>> 9238fb704d65b36db2dbaa18eda890ad49887380
