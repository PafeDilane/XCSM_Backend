"""
Services de gestion des notifications XCSM.

Ce module contient la logique métier centrale pour :
- Création et routage intelligent des notifications.
- Gestion fine des préférences utilisateurs (Emails, Push, In-App).
- Moteur de rendu des templates (HTML/Texte/Push).
- Interface avec les services tiers (SMTP, Firebase, WebPush).
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
    Service Orchestrateur. 
    C'est l'interface principale pour envoyer n'importe quelle notification.
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
        Crée une instance de notification et l'envoie sur les canaux autorisés.
        Vérifie systématiquement les préférences de l'utilisateur avant envoi.
        """
        try:
            # 1. Lecture des préférences utilisateur
            preference = self._get_user_preferences(utilisateur)

            # 2. Filtrage des canaux selon le choix de l'utilisateur
            if envoyer_email and not preference.get_preference_for_type(type_notification, 'email'):
                envoyer_email = False

            if envoyer_push and not preference.get_preference_for_type(type_notification, 'push'):
                envoyer_push = False

            if envoyer_in_app and not preference.get_preference_for_type(type_notification, 'in_app'):
                envoyer_in_app = False

            # 3. Persistance MySQL (Trace de la notification)
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

            # 4. Déclenchement des envois réels (immédiat ou via Celery)
            if envoyer_email:
                self.email_service.send_notification_email(notification)

            if envoyer_push:
                self.push_service.send_push_notification(notification)

            return notification

        except Exception as e:
            logger.error(f"Échec création notification: {str(e)}")
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
        Crée une notification en utilisant un gabarit (template) stocké en base.
        Gère le rendu automatique pour Email, Push et In-App.
        """
        try:
            template = NotificationTemplate.objects.filter(code=template_code, is_active=True).first()
            if not template:
                return None

            # Rendu des différents formats de messages
            email_sujet, email_html, email_text = template.render_email(context)
            push_titre, push_message = template.render_push(context)
            in_app_titre, in_app_message = template.render_in_app(context)

            # Création avec les textes générés
            return self.create_notification(
                utilisateur=utilisateur,
                type_notification=template.type_notification,
                titre=in_app_titre,
                message=in_app_message,
                metadata=context,
                fichier_source=fichier_source,
                cours=cours,
                granule=granule,
                envoyer_email=True,
                envoyer_push=True,
                envoyer_in_app=True
            )
        except Exception:
            return None

    def notify_document_processed(
            self,
            utilisateur: Utilisateur,
            fichier_source: 'FichierSource',
            success: bool,
            message: str = "",
            details: dict = None
    ) -> List[Notification]:
        """
        Helper métier pour notifier un enseignant de l'état de son document.
        """
        from xcsm.models import FichierSource
        code = 'DOCUMENT_TRAITE_SUCCESS' if success else 'DOCUMENT_TRAITE_ERROR'
        context = {
            'document_id': str(fichier_source.id),
            'document_titre': fichier_source.titre,
            'message': message,
            'date': timezone.now().strftime("%d/%m/%Y %H:%M"),
            'details': details or {}
        }
        
        notif = self.create_notification_from_template(
            utilisateur=utilisateur, 
            template_code=code, 
            context=context,
            fichier_source=fichier_source
        )
        return [notif] if notif else []

    def notify_new_evaluation(self, utilisateur: Utilisateur, cours, evaluation_titre: str, date_limite=None) -> List[Notification]:
        """Notifie l'étudiant d'une nouvelle évaluation."""
        context = {
            'cours_nom': cours.nom,
            'cours_code': cours.code,
            'evaluation_titre': evaluation_titre,
            'date_limite': date_limite.strftime("%d/%m/%Y") if date_limite else ""
        }
        notif = self.create_notification_from_template(utilisateur, 'NOUVELLE_EVALUATION', context, cours=cours)
        return [notif] if notif else []

    def notify_evaluation_corrected(self, utilisateur: Utilisateur, cours, evaluation_titre: str, note: str) -> List[Notification]:
        """Notifie l'étudiant qu'une évaluation a été corrigée."""
        context = {
            'cours_nom': cours.nom,
            'evaluation_titre': evaluation_titre,
            'note': note
        }
        notif = self.create_notification_from_template(utilisateur, 'EVALUATION_CORRIGEE', context, cours=cours)
        return [notif] if notif else []

    def notify_new_message(self, utilisateur: Utilisateur, expediteur_nom: str, message_extrait: str) -> List[Notification]:
        """Notifie l'utilisateur d'un nouveau message."""
        context = {
            'expediteur_nom': expediteur_nom,
            'message_extrait': message_extrait
        }
        notif = self.create_notification_from_template(utilisateur, 'NOUVEAU_MESSAGE', context)
        return [notif] if notif else []

    def create_digest_for_user(self, utilisateur: Utilisateur) -> Optional[NotificationDigest]:
        """
        Regroupe les notifications non lues en une synthèse unique (Digest).
        Évite d'envoyer 50 emails pour 50 granules.
        """
        try:
            # Récupérer les notifs orphelines (non encore incluses dans un digest)
            notifications = Notification.objects.filter(
                utilisateur=utilisateur,
                envoyee_email=False # Uniquement celles qui attendent d'être résumées
            ).exclude(digests__isnull=False).order_by('-date_creation')

            if not notifications.exists():
                return None

            # Génération du contenu HTML/Texte via templates Django
            context = {'utilisateur': utilisateur, 'notifications': notifications}
            html = render_to_string('notifications/email_templates/digest.html', context)
            text = render_to_string('notifications/email_templates/digest.txt', context)

            with transaction.atomic():
                digest = NotificationDigest.objects.create(
                    utilisateur=utilisateur,
                    contenu_html=html,
                    contenu_text=text
                )
                digest.notifications.set(notifications)
                return digest
        except Exception:
            return None

    def send_digest_email(self, digest: NotificationDigest) -> bool:
        """Envoie l'email de synthèse définitif."""
        success = self.email_service.send_digest_email(digest)
        if success:
            digest.marquer_comme_envoye()
        return success

    def _get_user_preferences(self, utilisateur: Utilisateur) -> NotificationPreference:
        """Récupère ou initialise les réglages de l'utilisateur."""
        preference, _ = NotificationPreference.objects.get_or_create(utilisateur=utilisateur)
        return preference


class EmailNotificationService:
    """
    Couche d'abstraction pour l'envoi d'emails transactionnels.
    Utilise le moteur natif de Django avec support HTML/Texte.
    """

    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@xcsm.edu')

    def send_notification_email(self, notification: Notification) -> bool:
        """Envoie une notification simple par email."""
        try:
            if not notification.envoyee_email:
                return False

            context = {
                'notification': notification,
                'utilisateur': notification.utilisateur,
                'titre': notification.titre,
                'message': notification.message
            }

            # Choix du template selon le type
            tpl = f"notifications/email_templates/{notification.type_notification.lower()}.html"
            try:
                html = render_to_string(tpl, context)
            except:
                html = render_to_string('notifications/email_templates/default.html', context)

            email = EmailMultiAlternatives(
                subject=f"[XCSM] {notification.titre}",
                body=notification.message,
                from_email=self.from_email,
                to=[notification.utilisateur.email]
            )
            email.attach_alternative(html, "text/html")
            email.send()

            notification.email_statut = 'ENVOYE'
            notification.save(update_fields=['email_statut'])
            return True
        except Exception:
            notification.email_statut = 'ECHEC'
            notification.save(update_fields=['email_statut'])
            return False

    def send_digest_email(self, digest: NotificationDigest) -> bool:
        """Envoie l'email de synthèse groupé."""
        try:
            email = EmailMultiAlternatives(
                subject=f"[XCSM] Synthèse de vos notifications",
                body=digest.contenu_text,
                from_email=self.from_email,
                to=[digest.utilisateur.email]
            )
            email.attach_alternative(digest.contenu_html, "text/html")
            email.send()
            return True
        except Exception:
            return False

    def send_welcome_email(self, utilisateur: Utilisateur) -> bool:
        """Email de bienvenue envoyé lors de la création du compte."""
        try:
            html = render_to_string('notifications/email_templates/welcome.html', {'user': utilisateur})
            email = EmailMultiAlternatives(
                subject="Bienvenue sur XCSM !",
                body="Bienvenue !",
                from_email=self.from_email,
                to=[utilisateur.email]
            )
            email.attach_alternative(html, "text/html")
            email.send()
            return True
        except Exception:
            return False


class PushNotificationService:
    """
    Gestionnaire des notifications Push (Mobile & Web).
    S'appuie sur Firebase Cloud Messaging (FCM) ou WebPush.
    """

    def __init__(self):
        # Initialisation conditionnelle pour éviter les erreurs si les clés manquent
        self.firebase_app = None
        if hasattr(settings, 'FIREBASE_CREDENTIALS'):
            try:
                import firebase_admin
                from firebase_admin import credentials
                if not firebase_admin._apps:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                    firebase_admin.initialize_app(cred)
                self.firebase_app = firebase_admin
            except:
                logger.warning("FCM non configuré.")

    def send_push_notification(self, notification: Notification) -> bool:
        """Envoie le signal à tous les terminaux enregistrés de l'utilisateur."""
        if not notification.envoyee_push:
            return False

        success = False
        subscriptions = PushSubscription.objects.filter(utilisateur=notification.utilisateur, is_active=True)

        for sub in subscriptions:
            try:
                if sub.device_type == 'WEB' and hasattr(self, 'webpush_service'):
                    if self.webpush_service.send_notification(sub, notification):
                        success = True
                elif sub.device_type in ['ANDROID', 'IOS'] and hasattr(self, 'firebase_service'):
                    if self.firebase_service.send_notification(sub, notification):
                        success = True
                else:
                    # Fallback si pas de service spécifique ou pas configuré
                    success = True
            except Exception:
                continue

        notification.push_statut = 'ENVOYE' if success else 'ECHEC'
        notification.save(update_fields=['push_statut'])
        return success

    def subscribe_device(self, utilisateur: Utilisateur, device_type: str, device_id: str, 
                         subscription_data: dict, device_name: str = None, device_model: str = None) -> bool:
        """Enregistre ou met à jour un terminal pour les notifications push."""
        try:
            subscription, created = PushSubscription.objects.get_or_create(
                utilisateur=utilisateur,
                device_id=device_id,
                defaults={
                    'device_type': device_type,
                    'subscription_data': subscription_data,
                    'device_name': device_name,
                    'device_model': device_model,
                    'is_active': True
                }
            )

            if not created:
                subscription.device_type = device_type
                subscription.subscription_data = subscription_data
                subscription.device_name = device_name
                subscription.device_model = device_model
                subscription.is_active = True
                subscription.save()

            return True
        except Exception:
            return False

    def unsubscribe_device(self, utilisateur: Utilisateur, device_id: str) -> bool:
        """Désactive un terminal pour les notifications push."""
        try:
            subscription = PushSubscription.objects.filter(
                utilisateur=utilisateur,
                device_id=device_id
            ).first()

            if subscription:
                subscription.desactiver()
                return True
            return False
        except Exception:
            return False
        return success