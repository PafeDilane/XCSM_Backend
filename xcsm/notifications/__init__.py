"""
Package des notifications XCSM.

Ce module gère l'envoi et la gestion des notifications :
- Notifications in-app
- Emails transactionnels
- Notifications push (mobile et web)
"""

default_app_config = 'xcsm.notifications.apps.NotificationsConfig'

# Types de notifications supportés
NOTIFICATION_TYPES = {
    'DOCUMENT_TRAITE': {
        'code': 'DOCUMENT_TRAITE',
        'name': 'Document traité',
        'description': 'Un document a été traité avec succès',
        'channels': ['in_app', 'email']
    },
    'DOCUMENT_ERREUR': {
        'code': 'DOCUMENT_ERREUR',
        'name': 'Erreur de traitement',
        'description': 'Une erreur est survenue lors du traitement',
        'channels': ['in_app', 'email']
    },
    'NOUVELLE_EVALUATION': {
        'code': 'NOUVELLE_EVALUATION',
        'name': 'Nouvelle évaluation',
        'description': 'Une nouvelle évaluation a été publiée',
        'channels': ['in_app', 'email', 'push']
    },
    'EVALUATION_CORRIGEE': {
        'code': 'EVALUATION_CORRIGEE',
        'name': 'Évaluation corrigée',
        'description': 'La correction d\'une évaluation est disponible',
        'channels': ['in_app', 'email']
    },
    'NOUVEAU_MESSAGE': {
        'code': 'NOUVEAU_MESSAGE',
        'name': 'Nouveau message',
        'description': 'Un nouveau message a été posté',
        'channels': ['in_app', 'push']
    },
    'SYSTEM_MAINTENANCE': {
        'code': 'SYSTEM_MAINTENANCE',
        'name': 'Maintenance système',
        'description': 'Maintenance planifiée du système',
        'channels': ['in_app', 'email']
    },
    'PROFIL_MIS_A_JOUR': {
        'code': 'PROFIL_MIS_A_JOUR',
        'name': 'Profil mis à jour',
        'description': 'Votre profil a été mis à jour avec succès',
        'channels': ['in_app']
    }
}

# Canaux de notification
CHANNELS = {
    'IN_APP': 'in_app',
    'EMAIL': 'email',
    'PUSH': 'push'
}