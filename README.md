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
        }
      ]
    }
  ]
}
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


