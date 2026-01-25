
# Système de Notifications XCSM

## Vue d'ensemble
Système complet de notifications pour la plateforme XCSM, supportant :
- Notifications in-app
- Emails transactionnels
- Notifications push (web et mobile)

## Architecture

```
xcsm/notifications/
├── models.py              # Modèles de données
├── serializers.py         # Serializers DRF
├── views.py               # Vues API
├── services.py            # Logique métier
├── tasks.py               # Tâches Celery (asynchrone)
├── signals.py             # Signaux Django
├── email_templates/       # Templates d'emails
├── push/                  # Notifications push
└── tests/                 # Tests unitaires
```

## 🔧 Installation

### Dépendances
```bash
# Pour les emails
pip install django-templated-mail

# Pour les notifications push web
pip install pywebpush py-vapid

# Pour Firebase (push mobile)
pip install firebase-admin
```

### Configuration
```python
# settings.py

# Emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
DEFAULT_FROM_EMAIL = 'XCSM <noreply@xcsm.edu>'

# Web Push (VAPID)
WEBPUSH_PRIVATE_KEY = 'votre-cle-privee'
WEBPUSH_PUBLIC_KEY = 'votre-cle-publique'
WEBPUSH_CLAIM_EMAIL = 'contact@xcsm.edu'

# Firebase
FIREBASE_CREDENTIALS = 'chemin/vers/firebase-credentials.json'
FIREBASE_PROJECT_ID = 'votre-projet-id'
```

### Migrations
```bash
python manage.py makemigrations notifications
python manage.py migrate
```

## API Endpoints

### Notifications
- `GET /api/v1/notifications/` - Liste des notifications
- `GET /api/v1/notifications/{id}/` - Détail d'une notification
- `POST /api/v1/notifications/mark-as-read/` - Marquer comme lues
- `GET /api/v1/notifications/unread-count/` - Nombre de non lues

### Préférences
- `GET /api/v1/notification-preferences/` - Préférences de l'utilisateur
- `PUT /api/v1/notification-preferences/{id}/` - Mettre à jour

### Abonnements Push
- `GET /api/v1/push-subscriptions/` - Liste des abonnements
- `POST /api/v1/push-subscriptions/` - Créer un abonnement
- `POST /api/v1/push-subscriptions/unsubscribe/` - Désabonner

### Templates (Admin)
- `GET /api/v1/notification-templates/` - Liste des templates
- `POST /api/v1/notification-templates/` - Créer un template

## 🚀 Utilisation

### Créer une notification
```python
from xcsm.notifications.services import NotificationService

service = NotificationService()

notification = service.create_notification(
    utilisateur=user,
    type_notification='DOCUMENT_TRAITE',
    titre='Document traité',
    message='Votre document a été traité avec succès.',
    metadata={'document_id': '123'},
    envoyer_email=True,
    envoyer_push=False,
    envoyer_in_app=True
)
```

### Notifier un document traité
```python
service.notify_document_processed(
    utilisateur=user,
    fichier_source=document,
    success=True,
    message='Document traité avec succès',
    details={'pages': 25, 'granules': 150}
)
```

### Créer depuis un template
```python
notification = service.create_notification_from_template(
    utilisateur=user,
    template_code='DOCUMENT_TRAITE_SUCCESS',
    context={
        'document_titre': 'Introduction à Python',
        'processing_time': '3.5s',
        'granules_count': 189
    },
    fichier_source=document
)
```

## Types de Notifications

### Supportés
1. **DOCUMENT_TRAITE** - Document traité avec succès
2. **DOCUMENT_ERREUR** - Erreur de traitement
3. **NOUVELLE_EVALUATION** - Nouvelle évaluation publiée
4. **EVALUATION_CORRIGEE** - Correction disponible
5. **NOUVEAU_MESSAGE** - Nouveau message
6. **SYSTEM_MAINTENANCE** - Maintenance système
7. **PROFIL_MIS_A_JOUR** - Profil mis à jour

### Canaux par défaut
- In-app : Tous les types
- Email : DOCUMENT_TRAITE, DOCUMENT_ERREUR, SYSTEM_MAINTENANCE
- Push : NOUVELLE_EVALUATION, NOUVEAU_MESSAGE

## Tests

### Exécution des tests
```bash
# Tous les tests
python manage.py test xcsm.notifications.tests

# Tests spécifiques
python manage.py test xcsm.notifications.tests.test_models
python manage.py test xcsm.notifications.tests.test_services
python manage.py test xcsm.notifications.tests.test_views
```

### Couverture des tests
```bash
coverage run --source='xcsm.notifications' manage.py test xcsm.notifications.tests
coverage report
coverage html
```

## Tâches Celery

### Configuration
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Planification des tâches
CELERY_BEAT_SCHEDULE = {
    'create-digests-daily': {
        'task': 'xcsm.notifications.tasks.create_digests_for_users_task',
        'schedule': crontab(hour=6, minute=0),  # Tous les jours à 6h
    },
    'cleanup-old-notifications': {
        'task': 'xcsm.notifications.tasks.cleanup_old_notifications_task',
        'schedule': crontab(hour=2, minute=0, day_of_week='sunday'),  # Dimanche à 2h
    },
}
```

### Tâches disponibles
1. `send_notification_email_task` - Envoyer un email
2. `send_bulk_notifications_task` - Notifications en masse
3. `create_digests_for_users_task` - Créer des synthèses
4. `cleanup_old_notifications_task` - Nettoyage
5. `retry_failed_notifications_task` - Relancer les échecs

## 📊 Monitoring

### Métriques
- Nombre de notifications envoyées
- Taux de lecture
- Taux d'échec d'envoi
- Temps de réponse des services

### Logs
Les logs sont disponibles dans :
- `logs/notifications_info.log` - Informations générales
- `logs/notifications_error.log` - Erreurs
- `logs/notifications_email.log` - Envois d'emails
- `logs/notifications_push.log` - Notifications push

## Sécurité

### Protection des données
- Tokens push chiffrés
- Données personnelles anonymisées dans les logs
- Validation des abonnements push
- Rate limiting sur les endpoints

### Permissions
- Utilisateurs : Lecture de leurs propres notifications
- Enseignants : Notification de leurs documents
- Admins : Accès complet, création en masse

## Dépannage

### Problèmes courants

#### Emails non envoyés
1. Vérifier la configuration SMTP
2. Vérifier les logs `notifications_email.log`
3. Tester avec `send_test_email_task`

#### Notifications push non reçues
1. Vérifier les abonnements dans la base
2. Vérifier la configuration VAPID/Firebase
3. Tester avec `send_test_notification`

#### Performances
1. Utiliser les tâches Celery pour les envois en masse
2. Configurer le cache pour les requêtes fréquentes
3. Nettoyer régulièrement les anciennes notifications

### Commandes utiles
```bash
# Tester le système d'email
python manage.py send_test_email user@example.com

# Vérifier les abonnements push
python manage.py check_push_subscriptions

# Nettoyer manuellement
python manage.py cleanup_notifications --days=90

# Statistiques
python manage.py notification_stats
```

## 📈 Évolution

### Améliorations planifiées
1. **Analytics avancés** - Tracking des ouvertures/clics
2. **Segmentation** - Notifications ciblées par groupes
3. **A/B testing** - Tests de différents messages
4. **Personalisation** - Contenu dynamique basé sur le comportement
5. **Intégration** - Webhooks, Slack, Teams

### Extensibilité
Le système est conçu pour être facilement étendu :
- Ajout de nouveaux types de notifications
- Intégration de nouveaux services push
- Templates personnalisables
- Workflows de notification complexes

---

## Notes de version

### v1.0.0
- ✅ Notifications in-app complètes
- ✅ Emails transactionnels
- ✅ Push web (Web Push API)
- ✅ Push mobile (Firebase)
- ✅ Gestion des préférences utilisateur
- ✅ Templates de notifications
- ✅ Tâches asynchrones Celery
- ✅ Tests complets
- ✅ Documentation API

### Prochaines versions
- v1.1.0 : Analytics et tracking
- v1.2.0 : Segmentation avancée
- v1.3.0 : Intégrations tierces
```

## ✅ **BRANCHE `feature/notifications-system`**

### **Fichiers mis en place :**
1.  `xcsm/notifications/__init__.py` - Configuration du package
2.  `xcsm/notifications/models.py` - Modèles complets
3.  `xcsm/notifications/serializers.py` - Serializers DRF
4.  `xcsm/notifications/views.py` - Vues API complètes
5.  `xcsm/notifications/services.py` - Services métier
6.  `xcsm/notifications/tasks.py` - Tâches Celery
7.  `xcsm/notifications/signals.py` - Signaux Django
8.  `xcsm/notifications/email_templates/base.html` - Template de base
9.  `xcsm/notifications/email_templates/document_traite.html` - Template document traité
10.  `xcsm/notifications/email_templates/nouvelle_evaluation.html` - Template évaluation
11.  `xcsm/notifications/push/__init__.py` - Package push
12.  `xcsm/notifications/push/firebase_service.py` - Service Firebase
13.  `xcsm/notifications/push/webpush_service.py` - Service WebPush
14.  `xcsm/notifications/tests/__init__.py` - Package tests
15.  `xcsm/notifications/tests/test_models.py` - Tests modèles
16.  `xcsm/notifications/tests/test_services.py` - Tests services
17.  `xcsm/notifications/tests/test_views.py` - Tests vues


### **Fonctionnalités implémentées :**
-  Système de notifications multi-canaux (in-app, email, push)
-  Gestion des préférences utilisateur
-  Templates de notifications réutilisables
-  Services Firebase et WebPush
-  Tâches asynchrones avec Celery
-  Signaux Django pour automatisation
-  Tests unitaires complets
-  Documentation API Swagger/OpenAPI
-  Pagination, filtrage, recherche
-  Gestion des erreurs et retry

### **Commandes pour utiliser la branche :**
```bash
# Créer et basculer sur la branche
git checkout -b feature/notifications-system

# Ajouter tous les fichiers
git add xcsm/notifications/
git add README_NOTIFICATIONS.md

# Commit
git commit -m "feat: implémentation complète du système de notifications"

# Pousser
git push origin feature/notifications-system

# Revenir à main
git checkout main
```

La branche `feature/notifications-system` est maintenant **complète** et prête pour le merge ou les tests.

---