"""
Service Web Push API pour les notifications push dans les navigateurs.

Ce service gère l'envoi de notifications push aux navigateurs web
via la Web Push API utilisant le protocole VAPID.
"""
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

# Tentative d'importer pywebpush (optionnel)
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pywebpush non installé. Les notifications push web seront désactivées.")

from . import PushServiceError, PushSubscriptionError, PushNotificationError

logger = logging.getLogger(__name__)


class WebPushService:
    """
    Service pour envoyer des notifications push via Web Push API.
    """

    def __init__(self):
        """
        Initialise le service Web Push.

        Raises:
            PushConfigurationError: Si Web Push n'est pas configuré
        """
        if not WEBPUSH_AVAILABLE:
            self._initialized = False
            logger.warning("pywebpush non disponible")
            return

        # Configuration VAPID
        self.vapid_private_key = getattr(settings, 'WEBPUSH_PRIVATE_KEY', None)
        self.vapid_public_key = getattr(settings, 'WEBPUSH_PUBLIC_KEY', None)
        self.vapid_claim_email = getattr(settings, 'WEBPUSH_CLAIM_EMAIL', 'contact@xcsm.edu')

        if not all([self.vapid_private_key, self.vapid_public_key, self.vapid_claim_email]):
            logger.warning("Configuration VAPID incomplète. Les notifications push web seront désactivées.")
            self._initialized = False
            return

        self.webpush_settings = {
            'VAPID_PRIVATE_KEY': self.vapid_private_key,
            'VAPID_PUBLIC_KEY': self.vapid_public_key,
            'VAPID_CLAIM_EMAIL': self.vapid_claim_email,
        }

        self._initialized = True
        logger.info("Service Web Push initialisé avec succès")

    def is_initialized(self) -> bool:
        """
        Vérifie si le service Web Push est correctement initialisé.

        Returns:
            bool: True si initialisé, False sinon
        """
        return self._initialized and WEBPUSH_AVAILABLE

    def send_notification(
            self,
            subscription,
            notification
    ) -> bool:
        """
        Envoie une notification push via Web Push API.

        Args:
            subscription: L'abonnement push
            notification: La notification à envoyer

        Returns:
            bool: True si l'envoi a réussi, False sinon

        Raises:
            PushNotificationError: Si l'envoi échoue
        """
        if not self.is_initialized():
            logger.warning("Web Push non initialisé, notification ignorée")
            return False

        try:
            # Récupérer les données d'abonnement
            subscription_data = subscription.subscription_data

            # Valider les données d'abonnement
            if not self._validate_subscription_data(subscription_data):
                logger.error(f"Données d'abonnement invalides: {subscription.device_id}")
                raise PushSubscriptionError("Données d'abonnement invalides")

            # Préparer la charge utile de la notification
            payload = {
                'title': notification.titre[:100],  # Limiter la longueur
                'body': notification.message[:240],  # Limiter la longueur
                'icon': getattr(settings, 'WEBPUSH_ICON_URL', 'https://xcsm.edu/static/icons/icon-192x192.png'),
                'badge': getattr(settings, 'WEBPUSH_BADGE_URL', 'https://xcsm.edu/static/icons/badge-96x96.png'),
                'timestamp': int(timezone.now().timestamp() * 1000),  # Milliseconds
                'data': {
                    'notification_id': str(notification.id),
                    'type': notification.type_notification,
                    'url': self._get_notification_url(notification),
                }
            }

            # Ajouter les métadonnées si disponibles
            if notification.metadata:
                payload['data'].update({
                    f'metadata_{key}': str(value)
                    for key, value in notification.metadata.items()
                    if isinstance(value, (str, int, float, bool))
                })

            # Ajouter les IDs des objets liés
            if notification.fichier_source:
                payload['data']['fichier_source_id'] = str(notification.fichier_source.id)
            if notification.cours:
                payload['data']['cours_id'] = str(notification.cours.id)
            if notification.granule:
                payload['data']['granule_id'] = str(notification.granule.id)

            # Options d'envoi
            options = {
                'vapid_private_key': self.vapid_private_key,
                'vapid_claim_email': self.vapid_claim_email,
                'vapid_public_key': self.vapid_public_key,
                'ttl': 86400,  # Time to live: 24 heures
                'urgency': 'high',
            }

            # Envoyer la notification
            response = webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                **options
            )

            # Enregistrer l'ID du message (extraire de la réponse si possible)
            if hasattr(response, 'headers') and 'location' in response.headers:
                notification.push_message_id = response.headers['location']
                notification.save(update_fields=['push_message_id'])

            logger.info(f"Notification Web Push envoyée à {subscription.device_id}")
            return True

        except WebPushException as e:
            # Analyser l'exception pywebpush
            if e.response:
                status_code = e.response.status_code

                if status_code == 404 or status_code == 410:
                    # Abonnement introuvable ou expiré
                    logger.warning(f"Abonnement expiré: {subscription.device_id}")
                    subscription.desactiver()
                    return False

                elif status_code == 400:
                    # Requête invalide
                    logger.error(f"Requête Web Push invalide: {e.response.text}")
                    raise PushNotificationError(f"Requête invalide: {e.response.text}")

                elif status_code == 413:
                    # Payload trop grande
                    logger.error(f"Payload trop grande pour {subscription.device_id}")
                    raise PushNotificationError("Payload trop grande")

                elif status_code == 429:
                    # Trop de requêtes
                    logger.error(f"Trop de requêtes pour {subscription.device_id}")
                    raise PushNotificationError("Trop de requêtes")

            logger.error(f"Erreur Web Push: {str(e)}")
            raise PushNotificationError(f"Erreur Web Push: {str(e)}")

        except json.JSONEncodeError as e:
            logger.error(f"Erreur d'encodage JSON: {str(e)}")
            raise PushNotificationError(f"Erreur d'encodage: {str(e)}")

        except Exception as e:
            logger.error(f"Erreur Web Push inattendue: {str(e)}")
            raise PushNotificationError(f"Erreur inattendue: {str(e)}")

    def validate_subscription(self, subscription) -> bool:
        """
        Valide un abonnement Web Push.

        Args:
            subscription: L'abonnement à valider

        Returns:
            bool: True si l'abonnement est valide, False sinon
        """
        if not self.is_initialized():
            return False

        try:
            subscription_data = subscription.subscription_data

            # Validation basique des données d'abonnement
            if not self._validate_subscription_data(subscription_data):
                return False

            # Tenter d'envoyer une notification de test (optionnel)
            # Pour l'instant, on se contente d'une validation structurelle

            return True

        except Exception as e:
            logger.error(f"Erreur de validation d'abonnement: {str(e)}")
            return False

    def _validate_subscription_data(self, subscription_data: Dict[str, Any]) -> bool:
        """
        Valide la structure des données d'abonnement.

        Args:
            subscription_data: Données d'abonnement

        Returns:
            bool: True si valide, False sinon
        """
        try:
            # Vérifier la structure requise pour Web Push
            if not isinstance(subscription_data, dict):
                return False

            # Endpoint requis
            if 'endpoint' not in subscription_data:
                return False

            endpoint = subscription_data['endpoint']
            if not endpoint or not isinstance(endpoint, str):
                return False

            # Vérifier que l'endpoint est une URL valide
            if not endpoint.startswith(('https://', 'http://localhost')):
                return False

            # Clés requises pour le cryptage
            if 'keys' not in subscription_data:
                return False

            keys = subscription_data['keys']
            if not isinstance(keys, dict):
                return False

            # Vérifier les clés de cryptage
            if 'p256dh' not in keys or 'auth' not in keys:
                return False

            p256dh = keys['p256dh']
            auth = keys['auth']

            if not p256dh or not auth:
                return False

            # Vérifier le format base64 (approximatif)
            import base64
            import re

            # Vérifier p256dh (doit être base64 URL-safe)
            try:
                base64.urlsafe_b64decode(p256dh + '=' * (4 - len(p256dh) % 4))
            except:
                return False

            # Vérifier auth (doit être base64 URL-safe)
            try:
                base64.urlsafe_b64decode(auth + '=' * (4 - len(auth) % 4))
            except:
                return False

            return True

        except Exception as e:
            logger.error(f"Erreur de validation des données d'abonnement: {str(e)}")
            return False

    def _get_notification_url(self, notification) -> str:
        """
        Génère l'URL de destination pour une notification.

        Args:
            notification: La notification

        Returns:
            str: URL de destination
        """
        base_url = getattr(settings, 'FRONTEND_URL', 'https://xcsm.edu')

        # Déterminer l'URL en fonction du type de notification
        if notification.fichier_source:
            return f"{base_url}/documents/{notification.fichier_source.id}"
        elif notification.cours:
            return f"{base_url}/cours/{notification.cours.id}"
        elif notification.granule:
            return f"{base_url}/granules/{notification.granule.id}"
        else:
            return f"{base_url}/notifications"

    def create_vapid_keys(self) -> Dict[str, str]:
        """
        Crée une nouvelle paire de clés VAPID.

        Returns:
            Dict: Clés publique et privée

        Raises:
            PushConfigurationError: Si la génération échoue
        """
        try:
            from py_vapid import Vapid
            import base64

            # Générer les clés
            vapid = Vapid()
            vapid.generate_keys()

            # Récupérer les clés au format base64 URL-safe
            private_key = vapid.private_key
            public_key = vapid.public_key

            # Convertir en base64
            private_key_b64 = base64.urlsafe_b64encode(private_key).decode('utf-8').rstrip('=')
            public_key_b64 = base64.urlsafe_b64encode(public_key).decode('utf-8').rstrip('=')

            return {
                'private_key': private_key_b64,
                'public_key': public_key_b64
            }

        except ImportError:
            raise PushConfigurationError("py-vapid non installé")
        except Exception as e:
            raise PushConfigurationError(f"Erreur de génération VAPID: {str(e)}")

    def send_test_notification(
            self,
            subscription_data: Dict[str, Any],
            title: str = "Test Notification",
            body: str = "Ceci est une notification de test"
    ) -> bool:
        """
        Envoie une notification de test.

        Args:
            subscription_data: Données d'abonnement
            title: Titre de test
            body: Corps de test

        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not self.is_initialized():
            return False

        try:
            # Préparer la payload de test
            payload = {
                'title': title,
                'body': body,
                'icon': getattr(settings, 'WEBPUSH_ICON_URL', 'https://xcsm.edu/static/icons/icon-192x192.png'),
                'timestamp': int(timezone.now().timestamp() * 1000),
                'data': {
                    'test': True,
                    'timestamp': timezone.now().isoformat()
                }
            }

            # Options d'envoi
            options = {
                'vapid_private_key': self.vapid_private_key,
                'vapid_claim_email': self.vapid_claim_email,
                'vapid_public_key': self.vapid_public_key,
                'ttl': 3600,  # 1 heure
            }

            # Envoyer la notification
            webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                **options
            )

            logger.info("Notification de test envoyée avec succès")
            return True

        except WebPushException as e:
            logger.error(f"Erreur lors de l'envoi de test: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'envoi de test: {str(e)}")
            return False