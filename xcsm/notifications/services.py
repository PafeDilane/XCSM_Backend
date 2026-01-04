"""
Services de gestion des notifications XCSM.

Ce module contient la logique métier pour :
- Création et envoi de notifications
- Gestion des préférences utilisateur
- Envoi d'emails transactionnels
- Envoi de notifications push
- Gestion des templates
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db import transaction

from .models import (
    Notification,
    NotificationPreference,
    NotificationTemplate,
    PushSubscription,
    NotificationDigest
)
from xcsm.models import Utilisateur

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service principal pour la gestion des notifications.
    """

    def __init__(self):
        self.email_service = EmailNotificationService()
        self.push_service = PushNotificationService()

    def create_notification(
            self,
            utilisateur: Utilisateur,
            type_notification: str,
            titre: str,
            message: str,
            metadata: Optional[Dict[str, Any]] = None,
            fichier_source=None,
            cours=None,
            granule=None,
            envoyer_email: bool = False,
            envoyer_push: bool = False,
            envoyer_in_app: bool = True
    ) -> Notification:
        """
        Crée une notification pour un utilisateur.

        Args:
            utilisateur: L'utilisateur destinataire
            type_notification: Type de notification
            titre: Titre de la notification
            message: Message de la notification
            metadata: Métadonnées supplémentaires
            fichier_source: Fichier source lié (optionnel)
            cours: Cours lié (optionnel)
            granule: Granule lié (optionnel)
            envoyer_email: Envoyer par email
            envoyer_push: Envoyer par push
            envoyer_in_app: Afficher in-app

        Returns:
            La notification créée
        """
        try:
            # Vérifier les préférences de l'utilisateur
            preference = self._get_user_preferences(utilisateur)

            # Ajuster les canaux selon les préférences
            if envoyer_email and not preference.get_preference_for_type(type_notification, 'email'):
                envoyer_email = False

            if envoyer_push and not preference.get_preference_for_type(type_notification, 'push'):
                envoyer_push = False

            if envoyer_in_app and not preference.get_preference_for_type(type_notification, 'in_app'):
                envoyer_in_app = False

            # Créer la notification
            notification = Notification.objects.create(
                utilisateur=utilisateur,
                type_notification=type_notification,
                titre=titre,
                message=message,
                metadata=metadata or {},
                fichier_source=fichier_source,
                cours=cours,
                granule=granule,
                envoyee_email=envoyer_email,
                envoyee_push=envoyer_push,
                envoyee_in_app=envoyer_in_app
            )

            # Envoyer via les canaux sélectionnés
            if envoyer_email:
                self.email_service.send_notification_email(notification)

            if envoyer_push:
                self.push_service.send_push_notification(notification)

            logger.info(f"Notification créée: {notification.id} pour {utilisateur.username}")
            return notification

        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification: {str(e)}")
            raise

    def create_notification_from_template(
            self,
            utilisateur: Utilisateur,
            template_code: str,
            context: Dict[str, Any],
            fichier_source=None,
            cours=None,
            granule=None
    ) -> Optional[Notification]:
        """
        Crée une notification à partir d'un template.

        Args:
            utilisateur: L'utilisateur destinataire
            template_code: Code du template
            context: Contexte pour le rendu du template
            fichier_source: Fichier source lié
            cours: Cours lié
            granule: Granule lié

        Returns:
            La notification créée ou None en cas d'erreur
        """
        try:
            # Récupérer le template
            template = NotificationTemplate.objects.filter(
                code=template_code,
                is_active=True
            ).first()

            if not template:
                logger.error(f"Template non trouvé: {template_code}")
                return None

            # Rendre les templates
            email_sujet, email_html, email_text = template.render_email(context)
            push_titre, push_message = template.render_push(context)
            in_app_titre, in_app_message = template.render_in_app(context)

            # Créer la notification
            notification = self.create_notification(
                utilisateur=utilisateur,
                type_notification=template.type_notification,
                titre=in_app_titre,
                message=in_app_message,
                metadata=context,
                fichier_source=fichier_source,
                cours=cours,
                granule=granule,
                envoyer_email=True,  # Vérifié dans create_notification
                envoyer_push=True,   # Vérifié dans create_notification
                envoyer_in_app=True  # Vérifié dans create_notification
            )

            return notification

        except Exception as e:
            logger.error(f"Erreur lors de la création depuis template: {str(e)}")
            return None

    def notify_document_processed(
            self,
            utilisateur: Utilisateur,
            fichier_source,
            success: bool,
            message: str,
            details: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """
        Notifie un utilisateur du traitement d'un document.

        Args:
            utilisateur: L'utilisateur à notifier
            fichier_source: Le fichier source traité
            success: True si le traitement a réussi
            message: Message détaillé
            details: Détails supplémentaires

        Returns:
            Liste des notifications créées
        """
        notifications = []

        if success:
            # Notification de succès
            notification = self.create_notification_from_template(
                utilisateur=utilisateur,
                template_code='DOCUMENT_TRAITE_SUCCESS',
                context={
                    'document_titre': fichier_source.titre,
                    'document_id': str(fichier_source.id),
                    'message': message,
                    'details': details or {},
                    'date_traitement': timezone.now().isoformat()
                },
                fichier_source=fichier_source
            )
            if notification:
                notifications.append(notification)
        else:
            # Notification d'erreur
            notification = self.create_notification_from_template(
                utilisateur=utilisateur,
                template_code='DOCUMENT_TRAITE_ERROR',
                context={
                    'document_titre': fichier_source.titre,
                    'document_id': str(fichier_source.id),
                    'message': message,
                    'details': details or {},
                    'date_traitement': timezone.now().isoformat()
                },
                fichier_source=fichier_source
            )
            if notification:
                notifications.append(notification)

        return notifications

    def notify_new_evaluation(
            self,
            cours,
            evaluation_titre: str,
            date_limite: Optional[datetime] = None
    ) -> List[Notification]:
        """
        Notifie les étudiants d'un cours d'une nouvelle évaluation.

        Args:
            cours: Le cours concerné
            evaluation_titre: Titre de l'évaluation
            date_limite: Date limite de rendu

        Returns:
            Liste des notifications créées
        """
        notifications = []

        # Récupérer les étudiants du cours
        # Note: Cette logique dépendra de votre modèle d'inscription aux cours
        # Pour l'instant, on notifie tous les étudiants
        etudiants = Utilisateur.objects.filter(type_compte='ETUDIANT')

        for etudiant in etudiants:
            notification = self.create_notification_from_template(
                utilisateur=etudiant,
                template_code='NOUVELLE_EVALUATION',
                context={
                    'cours_titre': cours.titre,
                    'cours_code': cours.code,
                    'evaluation_titre': evaluation_titre,
                    'date_limite': date_limite.isoformat() if date_limite else None,
                    'enseignant': cours.enseignant.utilisateur.get_full_name()
                },
                cours=cours
            )
            if notification:
                notifications.append(notification)

        logger.info(f"{len(notifications)} notifications d'évaluation créées pour le cours {cours.titre}")
        return notifications

    def create_digest_for_user(
            self,
            utilisateur: Utilisateur,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Optional[NotificationDigest]:
        """
        Crée une synthèse de notifications pour un utilisateur.

        Args:
            utilisateur: L'utilisateur
            start_date: Date de début (défaut: dernière synthèse ou il y a 24h)
            end_date: Date de fin (défaut: maintenant)

        Returns:
            La synthèse créée ou None
        """
        try:
            # Déterminer les dates
            if not end_date:
                end_date = timezone.now()

            if not start_date:
                # Chercher la dernière synthèse
                last_digest = NotificationDigest.objects.filter(
                    utilisateur=utilisateur
                ).order_by('-date_creation').first()

                if last_digest:
                    start_date = last_digest.date_creation
                else:
                    start_date = end_date - timedelta(hours=24)

            # Récupérer les notifications non incluses dans une synthèse
            notifications = Notification.objects.filter(
                utilisateur=utilisateur,
                date_creation__gte=start_date,
                date_creation__lte=end_date
            ).exclude(
                digests__isnull=False
            ).order_by('-date_creation')

            if not notifications.exists():
                logger.debug(f"Aucune nouvelle notification pour {utilisateur.username}")
                return None

            # Créer le contenu de la synthèse
            context = {
                'utilisateur': utilisateur,
                'notifications': notifications,
                'start_date': start_date,
                'end_date': end_date,
                'notification_count': notifications.count()
            }

            # Rendre les templates
            html_content = render_to_string(
                'notifications/email_templates/digest.html',
                context
            )
            text_content = render_to_string(
                'notifications/email_templates/digest.txt',
                context
            )

            # Créer la synthèse
            with transaction.atomic():
                digest = NotificationDigest.objects.create(
                    utilisateur=utilisateur,
                    contenu_html=html_content,
                    contenu_text=text_content
                )

                # Associer les notifications
                digest.notifications.set(notifications)

                logger.info(f"Synthèse créée pour {utilisateur.username} avec {notifications.count()} notifications")
                return digest

        except Exception as e:
            logger.error(f"Erreur lors de la création de la synthèse: {str(e)}")
            return None

    def send_digest_email(self, digest: NotificationDigest) -> bool:
        """
        Envoie une synthèse par email.

        Args:
            digest: La synthèse à envoyer

        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Vérifier que l'utilisateur accepte les emails de synthèse
            preference = self._get_user_preferences(digest.utilisateur)
            if not preference.email_notifications_enabled:
                logger.debug(f"Emails désactivés pour {digest.utilisateur.username}")
                return False

            # Envoyer l'email
            success = self.email_service.send_digest_email(digest)

            if success:
                digest.marquer_comme_envoye()
                logger.info(f"Email de synthèse envoyé à {digest.utilisateur.email}")
            else:
                logger.error(f"Échec de l'envoi de l'email de synthèse à {digest.utilisateur.email}")

            return success

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la synthèse: {str(e)}")
            return False

    def _get_user_preferences(self, utilisateur: Utilisateur) -> NotificationPreference:
        """
        Récupère ou crée les préférences d'un utilisateur.

        Args:
            utilisateur: L'utilisateur

        Returns:
            Les préférences de notification
        """
        preference, created = NotificationPreference.objects.get_or_create(
            utilisateur=utilisateur
        )
        return preference


class EmailNotificationService:
    """
    Service d'envoi d'emails pour les notifications.
    """

    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@xcsm.edu')

    def send_notification_email(self, notification: Notification) -> bool:
        """
        Envoie une notification par email.

        Args:
            notification: La notification à envoyer

        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Vérifier si l'email doit être envoyé
            if not notification.envoyee_email:
                return False

            # Préparer le contexte
            context = {
                'notification': notification,
                'utilisateur': notification.utilisateur,
                'titre': notification.titre,
                'message': notification.message,
                'metadata': notification.metadata,
                'date_creation': notification.date_creation
            }

            # Ajouter les objets liés au contexte
            if notification.fichier_source:
                context['fichier_source'] = notification.fichier_source
            if notification.cours:
                context['cours'] = notification.cours
            if notification.granule:
                context['granule'] = notification.granule

            # Déterminer le template
            template_name = f"notifications/email_templates/{notification.type_notification.lower()}.html"

            try:
                html_content = render_to_string(template_name, context)
            except:
                # Template spécifique non trouvé, utiliser le template par défaut
                html_content = render_to_string(
                    'notifications/email_templates/default.html',
                    context
                )

            text_content = render_to_string(
                'notifications/email_templates/default.txt',
                context
            )

            # Préparer l'email
            email = EmailMultiAlternatives(
                subject=f"[XCSM] {notification.titre}",
                body=text_content,
                from_email=self.from_email,
                to=[notification.utilisateur.email],
                headers={
                    'X-Notification-ID': str(notification.id),
                    'X-Notification-Type': notification.type_notification
                }
            )
            email.attach_alternative(html_content, "text/html")

            # Envoyer l'email
            email.send()

            # Mettre à jour la notification
            notification.email_statut = 'ENVOYE'
            notification.save(update_fields=['email_statut'])

            logger.info(f"Email envoyé pour la notification {notification.id}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")

            # Marquer l'échec
            notification.email_statut = 'ECHEC'
            notification.save(update_fields=['email_statut'])

            return False

    def send_digest_email(self, digest: NotificationDigest) -> bool:
        """
        Envoie une synthèse de notifications par email.

        Args:
            digest: La synthèse à envoyer

        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Préparer le contexte
            context = {
                'digest': digest,
                'utilisateur': digest.utilisateur,
                'notifications': digest.notifications.all(),
                'date_creation': digest.date_creation
            }

            # Préparer l'email
            email = EmailMultiAlternatives(
                subject=f"[XCSM] Synthèse de vos notifications",
                body=digest.contenu_text,
                from_email=self.from_email,
                to=[digest.utilisateur.email],
                headers={
                    'X-Digest-ID': str(digest.id),
                    'X-Notification-Count': str(digest.notifications.count())
                }
            )
            email.attach_alternative(digest.contenu_html, "text/html")

            # Envoyer l'email
            email.send()

            logger.info(f"Email de synthèse envoyé: {digest.id}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de synthèse: {str(e)}")
            return False

    def send_welcome_email(self, utilisateur: Utilisateur) -> bool:
        """
        Envoie un email de bienvenue à un nouvel utilisateur.

        Args:
            utilisateur: Le nouvel utilisateur

        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            context = {
                'utilisateur': utilisateur,
                'date_inscription': timezone.now()
            }

            html_content = render_to_string(
                'notifications/email_templates/welcome.html',
                context
            )
            text_content = render_to_string(
                'notifications/email_templates/welcome.txt',
                context
            )

            email = EmailMultiAlternatives(
                subject="Bienvenue sur XCSM !",
                body=text_content,
                from_email=self.from_email,
                to=[utilisateur.email]
            )
            email.attach_alternative(html_content, "text/html")

            email.send()
            logger.info(f"Email de bienvenue envoyé à {utilisateur.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
            return False


class PushNotificationService:
    """
    Service d'envoi de notifications push.
    """

    def __init__(self):
        self.firebase_service = None
        self.webpush_service = None

        # Initialiser les services selon la configuration
        if hasattr(settings, 'FIREBASE_CREDENTIALS'):
            try:
                from .push.firebase_service import FirebasePushService
                self.firebase_service = FirebasePushService()
            except ImportError:
                logger.warning("Firebase non disponible, les notifications push mobiles seront désactivées")

        if hasattr(settings, 'WEBPUSH_SETTINGS'):
            try:
                from .push.webpush_service import WebPushService
                self.webpush_service = WebPushService()
            except ImportError:
                logger.warning("WebPush non disponible, les notifications push web seront désactivées")

    def send_push_notification(self, notification: Notification) -> bool:
        """
        Envoie une notification push.

        Args:
            notification: La notification à envoyer

        Returns:
            True si au moins un envoi a réussi, False sinon
        """
        if not notification.envoyee_push:
            return False

        success = False
        utilisateur = notification.utilisateur

        # Récupérer les abonnements actifs
        subscriptions = PushSubscription.objects.filter(
            utilisateur=utilisateur,
            is_active=True
        )

        for subscription in subscriptions:
            try:
                if subscription.device_type == 'WEB' and self.webpush_service:
                    self.webpush_service.send_notification(subscription, notification)
                    success = True

                elif subscription.device_type in ['ANDROID', 'IOS'] and self.firebase_service:
                    self.firebase_service.send_notification(subscription, notification)
                    success = True

            except Exception as e:
                logger.error(f"Erreur lors de l'envoi push à {subscription.device_id}: {str(e)}")

        # Mettre à jour le statut
        if success:
            notification.push_statut = 'ENVOYE'
        else:
            notification.push_statut = 'ECHEC'

        notification.save(update_fields=['push_statut'])
        return success

    def subscribe_device(
            self,
            utilisateur: Utilisateur,
            device_type: str,
            device_id: str,
            subscription_data: Dict[str, Any],
            device_name: Optional[str] = None,
            device_model: Optional[str] = None
    ) -> bool:
        """
        Enregistre un nouvel abonnement push.

        Args:
            utilisateur: L'utilisateur
            device_type: Type d'appareil
            device_id: ID unique de l'appareil
            subscription_data: Données d'abonnement
            device_name: Nom de l'appareil
            device_model: Modèle de l'appareil

        Returns:
            True si l'abonnement a réussi, False sinon
        """
        try:
            # Vérifier si un abonnement existe déjà
            existing = PushSubscription.objects.filter(
                device_id=device_id,
                utilisateur=utilisateur
            ).first()

            if existing:
                # Mettre à jour l'abonnement existant
                existing.subscription_data = subscription_data
                existing.device_name = device_name
                existing.device_model = device_model
                existing.is_active = True
                existing.save()
                logger.info(f"Abonnement push mis à jour pour {device_id}")
            else:
                # Créer un nouvel abonnement
                PushSubscription.objects.create(
                    utilisateur=utilisateur,
                    device_type=device_type,
                    device_id=device_id,
                    subscription_data=subscription_data,
                    device_name=device_name,
                    device_model=device_model
                )
                logger.info(f"Nouvel abonnement push pour {device_id}")

            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'abonnement push: {str(e)}")
            return False

    def unsubscribe_device(self, utilisateur: Utilisateur, device_id: str) -> bool:
        """
        Désinscrit un appareil des notifications push.

        Args:
            utilisateur: L'utilisateur
            device_id: ID de l'appareil

        Returns:
            True si la désinscription a réussi, False sinon
        """
        try:
            subscription = PushSubscription.objects.filter(
                device_id=device_id,
                utilisateur=utilisateur
            ).first()

            if subscription:
                subscription.desactiver()
                logger.info(f"Appareil {device_id} désinscrit")
                return True
            else:
                logger.warning(f"Abonnement non trouvé pour {device_id}")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la désinscription: {str(e)}")
            return False