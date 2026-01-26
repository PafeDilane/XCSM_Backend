# 📔 Guide Technique Approfondi : Architecture & Logique XCSM v2.0

**Auteur** : Antigravity AI pour HDBB  
**Contenu** : Explications exhaustives "Deep-Dive" sur l'implémentation du Backend.

---

## 1. 🔐 Authentification & Sécurité (UC01-UC04)

### 1.1 La Mécanique JWT (JSON Web Tokens)

Nous n'utilisons pas le système de sessions classique de Django car XCSM est une architecture **Stateless** (sans état).

- **Implémentation** : Basée sur `rest_framework_simplejwt`.
- **Fonctionnement** :
  - Au login, le serveur génère deux jetons : un `Access Token` (courte durée, 15 min) et un `Refresh Token` (longue durée, 7 jours).
  - **Sécurité Augmentée** : Nous avons activé la **Rotation des Refresh Tokens**. Dès qu'un refresh token est utilisé, il est invalidé et remplacé par un nouveau.
  - **Blacklisting** : À la déconnexion, le refresh token est ajouté à une "liste noire" en base de données pour empêcher toute réutilisation malveillante. (Modèle : `OutstandingToken`).

### 1.2 Création Automatique de Profils (Signaux)

Le professeur pourrait demander : "Comment assurez-vous qu'un étudiant a bien un profil Etudiant à l'inscription ?"

- **Réponse** : Via les **Django Signals**. Dans `xcsm/signals.py`, nous écoutons l'événement `post_save` sur le modèle `Utilisateur`. Dès qu'un compte est créé, le signal détecte le `type_compte` et instancie automatiquement un objet `Enseignant` ou `Etudiant`. C'est du **découpage métier propre**.

---

## 2. 📢 Système de Notifications (L'Oshrestrateur)

Le système est construit sur un pattern de **Service d'Abstraction** (`xcsm/notifications/services.py`).

### 2.1 La Logique de Routage

Nous avons centralisé la logique dans `NotificationService`. Lorsqu'une action survient (ex: document traité), le service :

1. Vérifie les **Préférences** de l'utilisateur (Email? Push? In-App?).
2. Utilise un **Gabarit (Template)** dynamique pour construire le message.
3. Délègue l'envoi aux sous-services : `EmailNotificationService` ou `PushNotificationService`.

### 2.2 Asynchronisme & Fiabilité

Pour ne pas ralentir l'utilisateur, les calculs de notifications et les envois d'emails groupés (Digests) sont gérés par **Celery**. Si le serveur d'email est temporairement indisponible, Celery réessaie l'envoi plus tard (`max_retries`).

---

## 3. 🧠 Traitement Sémantique (L'IA Backend)

C'est ici que réside la valeur ajoutée du projet : transformer un fichier binaire en savoir atomique.

### 3.1 Le Pipeline d'Extraction (`xcsm/processing.py`)

1. **Normalisation** : Conversion des formats PDF (via `PyMuPDF`), DOCX (via `Mammoth`) et TXT en un flux HTML structuré.
2. **Analyse de Structure** : Un algorithme détecte les titres (H1, H2) par heuristique (casse, ponctuation, longueur).
3. **Fragmentation (Granulation)** : Le texte est découpé en "Granules". Un granule est l'unité pédagogique minimale (un paragraphe, une définition, une question de quizz).

### 3.2 L'Architecture Hybride MySQL + MongoDB

Le professeur demandera sûrement : "Pourquoi deux bases de données ?"

- **Réponse** :
  - **MySQL** : Pour la **structure relationnelle**. C'est là qu'on définit que "Le Chapitre 1 contient la Section 2". MySQL est imbattable pour l'intégrité référentielle.
  - **MongoDB** : Pour la **flexibilité sémantique**. Le contenu brut des granules est stocké en JSON/HTML dans Mongo. Cela permet de supporter des contenus riches (formules, balises) sans alourdir le schéma relationnel de MySQL. Les deux sont liés par un `mongo_contenu_id`.

---

## 4. 🛡️ Résilience & Hardening (Le Blindage)

### 4.1 Global Exception Handler (`xcsm/exceptions.py`)

Le backend utilise un "Intercepteur de Crash".

- **Logique** : Toute exception levée dans une vue (ex: `DatabaseDown`, `PermissionError`, `Timeout`) passe par ce handler.
- **Bénéfice** : Au lieu d'une page d'erreur 500 illisible, le client reçoit toujours un JSON structuré décrivant l'erreur. Cela rend l'API **professionnelle et débuggable**.

### 4.2 Protection des Signaux

Nous avons "isolé" les signaux. Si le système de log d'audit échoue, cela ne fait jamais planter l'action principale. C'est le principe de **Dégradation Gracieuse**.

---

## 5. 🚜 Tâches de Fond (Celery & Redis)

- **Celery** est notre "moteur industriel". Il traite en arrière-plan les tâches qui prennent plus de 500ms :
  - Extraction lourde de documents.
  - Génération de rapports d'erreurs.
  - Envois massifs de notifications.
- **Redis** sert de "gare de triage" (Message Broker). Il stocke temporairement les messages que Celery doit traiter.

---

## 6. 📂 Cartographie des Dossiers (Pour l'orientation)

- `/xcsm/models.py` : Le **Plan** (Schéma MySQL).
- `/xcsm/serializers.py` : Les **Traducteurs** (Django Object <-> JSON).
- `/xcsm/views.py` : Les **Aiguilleurs** (Logique de requête HTTP).
- `/xcsm/json_utils.py` : Le **Pont** avec MongoDB.
- `/xcsm/processing.py` : L'**Usine** (Parsing & Extraction).

---
*Ce guide est la "bible" technique de votre projet. Appropriez-vous ces termes (`Stateless`, `Pattern Service`, `Heuristique`, `Granulation`, `Intégrité Référentielle`) pour briller lors de l'oral.*
