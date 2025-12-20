# XCSM_Backend
Backend de L'application XCSM en Django

# XCSM Backend - API de Traitement et Structuration de Contenus Pédagogiques

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

MySQL + MongoDB (Production Recommandée)**

MySQL (Métadonnées)** :
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

# Démarrage service
sudo systemctl start mongod
sudo systemctl enable mongod

# Vérification
mongosh --eval "db.version()"
```

Configuration connexion MongoDB :
javascript
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
