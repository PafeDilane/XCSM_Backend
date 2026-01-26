# 🎭 Scénario de Démonstration Officiel : XCSM v2.0

**Projet** : Extraction et Consultation Sémantique de Documents  
**Intervenant** : HDBB  
**Rôles** : Brian Brusly (Enseignant Expert), Pafe Dilane (Étudiant)

---

## 🏁 Prologue : État Zéro (L'Effet de propreté)

*Avant que le professeur n'arrive :*

1. Lancez `./reset_demo.sh` dans votre terminal.
2. **Ce que vous montrez :** "Monsieur, avant de commencer, j'ai réinitialisé l'intégralité de l'écosystème (MySQL et MongoDB) pour vous montrer une plateforme propre et fonctionnelle en temps réel."

---

## 👨‍🏫 Acte 1 : Brian Brusly et la Gestion de Savoir (UC01-UC04 / UC06-UC08)

### 1.1 Connexion Sécurisée (UC02)

* **Action** : Connectez-vous sur `/api/v1/auth/login/` avec `brian_brusly` / `XCSM_Test_Password_2026`.
* **Argument technique** : "Nous utilisons une authentification par **JWT (JSON Web Token)** avec rotation de jetons. Regardez la réponse : l'utilisateur reçoit ses tokens et ses informations de profil dès le login."

### 1.2 Audit et Historique (UC08 - Très apprécié)

* **Action** : Allez sur `/api/v1/history/`.
* **Argument technique** : "Chaque mouvement sur la plateforme est tracé. Ici, on voit que dès la création du compte, Brian a déjà alimenté son catalogue. C'est le journal de traçabilité d'audit complet de la version 2.0."

---

## 🧠 Acte 2 : Le Cœur de l'IA Backend (UC05 / UC09 / MongoDB)

### 2.1 Extraction Sémantique en Direct (UC05)

* **Action** : Uploadez un fichier (ex: `DevOps.pdf`) via l'endpoint d'upload.
* **Observation** : Ouvrez un second terminal montrant les logs de Celery.
* **Argument technique** : "Monsieur, regardez le worker Celery. Le traitement est **asynchrone**. Le prof n'attend pas que le PDF de 50 pages soit lu pour continuer à naviguer. Le backend découpe le document en **unités atomiques (Granules)** directement injectées dans **MongoDB**."

### 2.2 La Preuve MongoDB (Le Double Cœur)

* **Action** : Lancez `./env/bin/python inspect_data.py`.
* **Argument technique** : "Nous avons une architecture hybride. Les métadonnées sont dans **MySQL** pour la robustesse, mais le contenu extrait est dans **MongoDB**. Nous avons actuellement plus de **6 000 granules** stockés, prêts pour la recherche sémantique."

---

## 🎓 Acte 3 : Le Portail Étudiant (UC13 - UC14)

### 3.1 Connexion Étudiant (UC13)

* **Action** : Switcher sur le profil `etu_pafe` (Pafe Dilane).
* **Argument technique** : "Passons côté étudiant. Pafe consulte son portail unifié."

### 3.2 Le Portail "Badge-Driven"

* **Action** : Allez sur `/api/v1/portal/`.
* **Argument technique** : "Ici, tout est trié par importance sémantique. Les badges bleus sont des **Cours**, les oranges des **Évaluations**, et les verts les **Corrections officielles**. C'est une vue synthétique qui agrège 4 Use Cases en une seule vision."

### 3.3 Recherche Sémantique (UC14)

* **Action** : Utilisez l'endpoint de recherche avec le mot "Docker" ou "CMS".
* **Argument technique** : "La recherche ne fouille pas seulement les titres, elle plonge dans les milliers de fragments de texte dans MongoDB pour extraire le bon granule pédagogique instantanément."

---

## 🛡️ Acte 4 : La Forteresse Résiliente (L'Effet "Wow")

### 4.1 Gestion des Exceptions (Chaos Testing)

* **Action** : Tapez une URL au hasard (ex: `/api/v1/ghost/`) ou tentez de modifier un cours sans être Brian.
* **Argument technique** : "Monsieur, vous pouvez essayer de faire planter le système. J'ai buildé un **Custom Exception Handler**. Le backend intercepte tout crash et renvoie une réponse JSON sécurisée, protégeant la structure du serveur."

### 4.2 Diagnostic Temps Réel

* **Action** : Lancez `./env/bin/python check_all_services.py`.
* **Argument technique** : "À tout moment, l'administrateur peut vérifier la santé de la pile : MySQL, MongoDB, Redis et Celery sont surveillés par nos scripts internes."

---

## 🎬 Épilogue : Scalabilité (Docker)

* **Action** : Montrer les fichiers `Dockerfile` et `docker-compose.yml`.
* **Argument technique** : "Pour finir, le projet est totalement **Dockerisé**. Il peut être déployé sur n'importe quel serveur Cloud en une commande : `docker-compose up`. La Version 2.0 est prête pour la mise en production."

---
*Fin du Scénario. (Prenez une pause pour les questions - Vous avez tout verrouillé).*
