# XCSM : Dossier de Conception Intégral (Version 2.0)

Ce document constitue la bibliographie technique de référence du projet **XCSM (Extraction et Consultation Sémantique de Documents)**. Il détaille l'architecture actuelle du backend, les choix technologiques prioritaires, et présente une vision complète pour le développement du frontend associé.

---

## 1. Architecture Système & Flux de Données

Le projet XCSM repose sur une **Architecture Hybride et Asynchrone**, conçue pour garantir à la fois l'intégrité des relations pédagogiques et la flexibilité nécessaire au traitement intelligent de texte.

### Les 3 Piliers de Persistance

1. **MySQL / MariaDB (Le Cœur Relationnel)** :
    - Rôle : Gère l'authentification (Utilisateurs/Profils), la hiérarchie pédagogique (Annuaires de cours, chapitres, sections) et les métadonnées critiques.
    - Principe : Garantit la cohérence des données via des clés étrangères strictes.
2. **MongoDB (Le Cœur Sémantique)** :
    - Rôle : Stocke les "Granulés" de contenu brut après extraction IA/Cloud.
    - Principe : Permet de stocker des structures JSON complexes sans schéma fixe, facilitant l'édition dynamique et la recherche plein-texte ultra-rapide.
3. **Redis (Le Cœur Temps-Réel)** :
    - Rôle : Broker pour les tâches asynchrones (Celery) et gestion du cache.

---

## 2. Bibliographie des Objets et Classes (Modèles MySQL)

### A. Gestion des Identités et des Accès (Utilisateurs)

- `Utilisateur` : Étend `AbstractUser`. Point d'entrée unique.
  - Attributs clés : `type_compte` (ADMIN, ENSEIGNANT, ETUDIANT), `photo_url`.
- `Enseignant` : Profil métier. Relié à `Utilisateur`.
  - Attributs : `specialite`, `departement`.
- `Etudiant` : Profil académique. Relié à `Utilisateur`.
  - Attributs : `matricule`, `niveau` (L1-M2), `filiere`.

### B. Structure Pédagogique (L'Arborescence)

- `Cours` : L'entité racine. Chaque cours appartient à un `Enseignant`.
  - Attributs : `titre`, `code` (Unique), `niveau`, `filiere`, `est_publie`.
- `Partie` / `Chapitre` / `Section` / `SousSection` : Modèles hiérarchiques permettant de reconstruire la "Table des Matières" officielle d'un cours.
- `Granule` : L'unité atomique de connaissance.
  - Relation : Rattaché à une `SousSection` et un `FichierSource`.
  - Clé technique : `mongo_contenu_id` (Lien direct vers MongoDB).

### C. Évaluation et Suivi

- `Evaluation` : Examens ou Quizz générés à partir d'un cours.
- `Correction` : Solutionnaire rattaché à une évaluation (`OneToOneField`).
- `ActionLog` : Journal de traçabilité (UC08). Enregistre : qui a fait quoi (Upload, Login, Publication) et quand.

---

## 3. Principes de Programmation & Design Pattern (Python/Django)

1. **Découplage par Signaux (`signals.py`)** :
    - Utilisation du pattern *Observer*. Dès qu'un utilisateur s'inscrit, un signal crée automatiquement son profil spécifique. Dès qu'un document est publié, un signal notifie les étudiants concernés.
2. **Sérialisation Avancée (`serializers.py`)** :
    - Les *Serializers* ne font pas que transformer les données en JSON ; ils valident la complexité des mots de passe (UC01), vérifient les droits de suppression (UC07) et injectent des "badges colorés" calculés à la volée.
3. **Permissions Granulaires (`permissions.py`)** :
    - Implémentation de classes comme `IsEnseignant` pour restreindre l'édition des cours aux propriétaires légitimes.
4. **Gestion de l'Environnement (`python-decouple`)** :
    - Toutes les configurations sensibles (clés MySQL, URI MongoDB, SECRET_KEY) sont externalisées dans un fichier `.env`.

---

## 4. Organisation des Fichiers & Dossiers (Cartographie)

### Dossier Racine `/`

- `manage.py` : Le chef d'orchestre des commandes Django.
- `requirements.txt` : Liste exhaustive des librairies (Django, DRF, PyMongo, Celery, etc.).

### Dossier Projet `/xcsm_project/`

- `settings.py` : Configuration globale (Bases de données, JWT, Timezone, Logging).
- `urls.py` : Routeur principal. Définit les points d'entrée `/api/v1/...`.
- `wsgi.py` / `asgi.py` : Ponts de communication pour le déploiement Web (Synchrone vs Asynchrone).
- `celery.py` : Configuration de l'agent de tâches de fond.

### Dossier Application `/xcsm/`

- `models.py` : Définition du schéma de données MySQL (Classes d'objets).
- `serializers.py` : Moteur de transformation Données <-> JSON.
- `views.py` : Logique métier métier (Controllers). Gère l'extraction, la publication et la consultation.
- `views_auth.py` : Dédié au cycle de vie des comptes (Login, Inscription, Reset Password).
- `json_utils.py` : Fonctions spécifiques pour le dialogue avec MongoDB.
- `processing.py` : Algorithmes de transformation des documents PDF/DOCX en structures granulaires.

---

## 5. Proposition Intégrale pour le Frontend

Pour valoriser cette architecture riche, le frontend doit être ultra-réactif et haut de gamme.

### Pile Technologique (Tech Stack)

- **Next.js 14+ (React Framework)** : Pour bénéficier du rendu côté serveur (SSR) et de performances optimales.
- **Tailwind CSS** : Pour un design moderne, épuré et entièrement responsive.
- **Shadcn/UI & Framer Motion** : Pour des composants premium avec des micro-animations fluides.
- **Lucide-React** : Jeu d'icônes vectorielles légères.

### Fonctionnalités UX Clés

1. **Tableau de Bord Étudiant "Badge-Driven"** :
    - Affichage trié par badges de couleurs : 🔵 **Cours** (Bleu), 🟠 **Évaluation** (Orange), 🟢 **Correction** (Vert).
    - Indicateurs visuels de complétion du profil.
2. **L'Éditeur "Granule Studio" (Mode Enseignant)** :
    - Interface WYSIWYG permettant de modifier directement le texte ou le HTML extrait (provenant de MongoDB).
    - Drag & Drop pour réorganiser les chapitres et les sections.
3. **Recherche Sémantique Interactive** :
    - Barre de recherche globale avec auto-complétion, cherchant dans le titre MySQL et le contenu MongoDB simultanément.
4. **Mode Sombre (Dark Mode)** :
    - Design "Eye-Care" prioritaire pour les sessions d'étude nocturnes.

---

## 6. Paramètres de Configuration (Settings & Sécurité)

- **Authentification** : JWT (Simple JWT). Les jetons expirent après 60 minutes avec rotation du jeton de rafraîchissement.
- **CORS (Cross-Origin Resource Sharing)** : Configuré pour n'autoriser que les domaines du frontend officiel.
- **Throttle (Limites de débit)** : Protection Anti-DDoS intégrée (ex: 1000 requêtes/heure par utilisateur).
- **Logging** : Traçabilité complète des erreurs backend dans `/logs/xcsm_errors.log`.

---

*Document produit par Antigravity AI pour l'équipe de développement XCSM. Version du 26 Janvier 2026.*
