"""
Service Firebase Cloud Messaging (FCM) pour les notifications push mobiles.

Ce service gère l'envoi de notifications push aux appareils Android et iOS
via Firebase Cloud Messaging.
"""
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings

from . import PushServiceError, PushSubscriptionError, PushNotificationError

logger = logging.getLogger(__name__)


class FirebasePushService:
    """
    Service pour envoyer des notifications push via Firebase Cloud Messaging.
    """

    def __init__(self):
        """
        Initialise le service Firebase.

        Raises:
            PushConfigurationError: Si Firebase n'est pas configuré
        """
        self.credentials_path = getattr(settings, 'FIREBASE_CREDENTIALS', None)
        self.project_id = getattr(settings, 'FIREBASE_PROJECT_ID', None)

        if not self.credentials_path or not self.project_id:
            logger.warning("Firebase non configuré. Les notifications push mobiles seront désactivées.")
            self._initialized = False
            return

        try:
            # Importer firebase-admin (optionnel)
            import firebase_admin
            from firebase_admin import credentials, messaging

            if not firebase_admin._apps:
                # Initialiser Firebase avec les credentials
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)

            self.messaging = messaging
            self._initialized = True

            logger.info("Service Firebase initialisé avec succès")

        except ImportError:
            logger.error("firebase-admin non installé. Installez-le avec: pip install firebase-admin")
            self._initialized = False
        except Exception as e:
            logger.error(f"Erreur d'initialisation Firebase: {str(e)}")
            self._initialized = False

    def is_initialized(self) -> bool:
        """
        Vérifie si le service Firebase est correctement initialisé.

        Returns:
            bool: True si initialisé, False sinon
        """
        return self._initialized

    def send_notification(
            self,
            subscription,
            notification
    ) -> bool:
        """
        Envoie une notification push via Firebase.

        Args:
            subscription: L'abonnement push
            notification: La notification à envoyer

        Returns:
            bool: True si l'envoi a réussi, False sinon

        Raises:
            PushNotificationError: Si l'envoi échoue
        """
        if not self._initialized:
            logger.warning("Firebase non initialisé, notification ignorée")
            return False

        try:
            # Récupérer le token FCM depuis les données d'abonnement
            subscription_data = subscription.subscription_data

            if 'token' not in subscription_data:
                logger.error(f"Token FCM manquant pour l'abonnement {subscription.device_id}")
                raise PushSubscriptionError("Token FCM manquant")

            device_token = subscription_data['token']

            # Préparer la notification FCM
            fcm_notification = self.messaging.Notification(
                title=notification.titre[:100],  # Limiter la longueur
                body=notification.message[:240]  # Limiter la longueur
            )

            # Préparer les données supplémentaires
            data = {
                'notification_id': str(notification.id),
                'type': notification.type_notification,
                'timestamp': notification.date_creation.isoformat(),
            }

            # Ajouter les métadonnées si disponibles
            if notification.metadata:
                for key, value in notification.metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        data[f'metadata_{key}'] = str(value)

            # Ajouter les IDs des objets liés
            if notification.fichier_source:
                data['fichier_source_id'] = str(notification.fichier_source.id)
            if notification.cours:
                data['cours_id'] = str(notification.cours.id)
            if notification.granule:
                data['granule_id'] = str(notification.granule.id)

            # Configurer le message selon le type d'appareil
            if subscription.device_type == 'ANDROID':
                message = self.messaging.Message(
                    notification=fcm_notification,
                    data=data,
                    token=device_token,
                    android=self.messaging.AndroidConfig(
                        priority='high',
                        notification=self.messaging.AndroidNotification(
                            channel_id='xscm_notifications',
                            sound='default'
                        )
                    )
                )
            elif subscription.device_type == 'IOS':
                message = self.messaging.Message(
                    notification=fcm_notification,
                    data=data,
                    token=device_token,
                    apns=self.messaging.APNSConfig(
                        headers={'apns-priority': '10'},
                        payload=self.messaging.APNSPayload(
                            aps=self.messaging.Aps(
                                sound='default',
                                badge=1,
                                content_available=True
                            )
                        )
                    )
                )
            else:
                logger.error(f"Type d'appareil non supporté: {subscription.device_type}")
                return False

            # Envoyer la notification
            response = self.messaging.send(message)

            logger.info(f"Notification Firebase envoyée: {response}")

            # Enregistrer l'ID du message
            notification.push_message_id = response
            notification.save(update_fields=['push_message_id'])

            return True

        except self.messaging.UnregisteredError as e:
            # L'appareil n'est plus enregistré, désactiver l'abonnement
            logger.warning(f"Appareil non enregistré: {subscription.device_id}")
            subscription.desactiver()
            return False

        except self.messaging.SenderIdMismatchError as e:
            logger.error(f"Erreur d'ID d'expéditeur: {str(e)}")
            raise PushNotificationError(f"Erreur d'ID d'expéditeur: {str(e)}")

        except self.messaging.QuotaExceededError as e:
            logger.error(f"Quota Firebase dépassé: {str(e)}")
            raise PushNotificationError(f"Quota dépassé: {str(e)}")

        except self.messaging.ThirdPartyAuthError as e:
            logger.error(f"Erreur d'authentification tierce: {str(e)}")
            raise PushNotificationError(f"Erreur d'authentification: {str(e)}")

        except Exception as e:
            logger.error(f"Erreur Firebase inattendue: {str(e)}")
            raise PushNotificationError(f"Erreur inattendue: {str(e)}")

    def validate_subscription(self, subscription) -> bool:
        """
        Valide un abonnement Firebase.

        Args:
            subscription: L'abonnement à valider

        Returns:
            bool: True si l'abonnement est valide, False sinon
        """
        if not self._initialized:
            return False

        try:
            subscription_data = subscription.subscription_data

            if 'token' not in subscription_data:
                return False

            device_token = subscription_data['token']

            # Vérifier rapidement le format du token
            # Les tokens FCM sont généralement de longueur ~152 caractères
            if len(device_token) < 100 or len(device_token) > 200:
                return False

            # Note: Une validation complète nécessiterait un appel à l'API Firebase
            # Pour l'instant, on fait une validation basique

            return True

        except Exception as e:
            logger.error(f"Erreur de validation d'abonnement: {str(e)}")
            return False

    def send_multicast_notification(
            self,
            device_tokens: list,
            title: str,
            body: str,
            data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envoie une notification à plusieurs appareils.

        Args:
            device_tokens: Liste des tokens d'appareils
            title: Titre de la notification
            body: Corps de la notification
            data: Données supplémentaires

        Returns:
            Dict: Résultats de l'envoi

        Raises:
            PushNotificationError: Si l'envoi échoue
        """
        if not self._initialized:
            raise PushConfigurationError("Firebase non initialisé")

        try:
            # Préparer le message multicast
            message = self.messaging.MulticastMessage(
                notification=self.messaging.Notification(
                    title=title[:100],
                    body=body[:240]
                ),
                data=data or {},
                tokens=device_tokens
            )

            # Envoyer les notifications
            response = self.messaging.send_multicast(message)

            logger.info(f"Notifications multicast envoyées: {response.success_count} succès, {response.failure_count} échecs")

            # Analyser les échecs
            failures = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failures.append({
                        'device_token': device_tokens[idx],
                        'error': str(resp.exception) if resp.exception else 'Unknown error'
                    })

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failures': failures
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi multicast: {str(e)}")
            raise PushNotificationError(f"Erreur multicast: {str(e)}")

    def subscribe_to_topic(
            self,
            device_token: str,
            topic: str
    ) -> bool:
        """
        Abonne un appareil à un topic Firebase.

        Args:
            device_token: Token de l'appareil
            topic: Topic auquel s'abonner

        Returns:
            bool: True si l'abonnement a réussi, False sinon
        """
        if not self._initialized:
            return False

        try:
            response = self.messaging.subscribe_to_topic([device_token], topic)

            if response.errors:
                logger.error(f"Erreur d'abonnement au topic: {response.errors}")
                return False

            logger.info(f"Appareil abonné au topic: {topic}")
            return True

        except Exception as e:
            logger.error(f"Erreur d'abonnement au topic: {str(e)}")
            return False

    def unsubscribe_from_topic(
            self,
            device_token: str,
            topic: str
    ) -> bool:
        """
        Désabonne un appareil d'un topic Firebase.

        Args:
            device_token: Token de l'appareil
            topic: Topic dont se désabonner

        Returns:
            bool: True si le désabonnement a réussi, False sinon
        """
        if not self._initialized:
            return False

        try:
            response = self.messaging.unsubscribe_from_topic([device_token], topic)

            if response.errors:
                logger.error(f"Erreur de désabonnement du topic: {response.errors}")
                return False

            logger.info(f"Appareil désabonné du topic: {topic}")
            return True

        except Exception as e:
            logger.error(f"Erreur de désabonnement du topic: {str(e)}")
            return False

    def send_to_topic(
            self,
            topic: str,
            title: str,
            body: str,
            data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Envoie une notification à tous les appareils abonnés à un topic.

        Args:
            topic: Topic cible
            title: Titre de la notification
            body: Corps de la notification
            data: Données supplémentaires

        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not self._initialized:
            return False

        try:
            message = self.messaging.Message(
                notification=self.messaging.Notification(
                    title=title[:100],
                    body=body[:240]
                ),
                data=data or {},
                topic=topic
            )

            response = self.messaging.send(message)

            logger.info(f"Notification envoyée au topic {topic}: {response}")
            return True

        except Exception as e:
            logger.error(f"Erreur d'envoi au topic: {str(e)}")
            return False