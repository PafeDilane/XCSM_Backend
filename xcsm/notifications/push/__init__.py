"""
Package pour les services de notifications push.

Ce module fournit les interfaces pour envoyer des notifications push
via différents services :
- Firebase Cloud Messaging (FCM) pour les appareils mobiles
- Web Push API pour les navigateurs web
"""

from .firebase_service import FirebasePushService
from .webpush_service import WebPushService

__all__ = ['FirebasePushService', 'WebPushService']


class PushServiceError(Exception):
    """Exception de base pour les erreurs des services push."""
    pass


class PushSubscriptionError(PushServiceError):
    """Erreur liée à un abonnement push."""
    pass


class PushNotificationError(PushServiceError):
    """Erreur lors de l'envoi d'une notification push."""
    pass


class PushConfigurationError(PushServiceError):
    """Erreur de configuration du service push."""
    pass