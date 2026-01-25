"""
Tâches Celery pour le système de notifications XCSM.

Ce module contient les tâches asynchrones pour :
- Envoi d'emails en masse
- Envoi de notifications push
- Création de synthèses
- Nettoyage des anciennes notifications
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from .models import (
    Notification,
    NotificationPreference,
    NotificationDigest,
    PushSubscription
)
from .services import NotificationService, EmailNotificationService
from xcsm.models import Utilisateur

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email_task(self, notification_id: str):
    """
    Tâche pour envoyer un email de notification.

    Args:
        notification_id: ID de la notification
    """
    try:
        # Récupérer la notification
        notification = Notification.objects.get(id=notification_id)

        # Envoyer l'email
        email_service = EmailNotificationService()
        success = email_service.send_notification_email(notification)

        if not success:
            raise Exception("Échec de l'envoi de l'email")

        logger.info(f"Email de notification envoyé: {notification_id}")

    except Notification.DoesNotExist:
        logger.error(f"Notification non trouvée: {notification_id}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")
        # Réessayer la tâche
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_notifications_task(
        self,
        user_ids: List[str],
        type_notification: str,
        titre: str,
        message: str,
        metadata: dict = None,
        envoyer_email: bool = False,
        envoyer_push: bool = False
):
    """
    Tâche pour envoyer des notifications en masse.

    Args:
        user_ids: Liste des IDs utilisateur
        type_notification: Type de notification
        titre: Titre de la notification
        message: Message de la notification
        metadata: Métadonnées supplémentaires
        envoyer_email: Envoyer par email
        envoyer_push: Envoyer par push
    """
    try:
        notification_service = NotificationService()
        created_count = 0

        for user_id in user_ids:
            try:
                utilisateur = Utilisateur.objects.get(id=user_id)

                notification = notification_service.create_notification(
                    utilisateur=utilisateur,
                    type_notification=type_notification,
                    titre=titre,
                    message=message,
                    metadata=metadata or {},
                    envoyer_email=envoyer_email,
                    envoyer_push=envoyer_push,
                    envoyer_in_app=True
                )

                if notification:
                    created_count += 1

                    # Envoyer l'email de manière asynchrone si demandé
                    if envoyer_email and notification.envoyee_email:
                        send_notification_email_task.delay(str(notification.id))

            except Exception as e:
                logger.error(f"Erreur pour l'utilisateur {user_id}: {str(e)}")
                continue

        logger.info(f"{created_count} notifications créées sur {len(user_ids)} utilisateurs")
        return created_count

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi en masse: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def create_digests_for_users_task():
    """
    Tâche périodique pour créer des synthèses de notifications.

    Cette tâche est exécutée périodiquement pour créer des synthèses
    pour les utilisateurs selon leur fréquence configurée.
    """
    try:
        notification_service = NotificationService()
        created_count = 0

        # Récupérer les utilisateurs avec des préférences de synthèse
        preferences = NotificationPreference.objects.filter(
            digest_frequency__gt=0,
            email_notifications_enabled=True
        ).select_related('utilisateur')

        for preference in preferences:
            try:
                # Vérifier si une synthèse est due
                last_digest = NotificationDigest.objects.filter(
                    utilisateur=preference.utilisateur
                ).order_by('-date_creation').first()

                if last_digest:
                    # Vérifier si suffisamment de temps s'est écoulé
                    next_digest_time = last_digest.date_creation + timedelta(
                        hours=preference.digest_frequency
                    )

                    if timezone.now() < next_digest_time:
                        continue

                # Créer la synthèse
                digest = notification_service.create_digest_for_user(
                    preference.utilisateur
                )

                if digest:
                    # Envoyer la synthèse par email
                    notification_service.send_digest_email(digest)
                    created_count += 1

            except Exception as e:
                logger.error(f"Erreur pour l'utilisateur {preference.utilisateur.username}: {str(e)}")
                continue

        logger.info(f"{created_count} synthèses créées et envoyées")
        return created_count

    except Exception as e:
        logger.error(f"Erreur lors de la création des synthèses: {str(e)}")
        raise


@shared_task
def send_welcome_emails_task(user_ids: List[str]):
    """
    Tâche pour envoyer des emails de bienvenue aux nouveaux utilisateurs.

    Args:
        user_ids: Liste des IDs des nouveaux utilisateurs
    """
    try:
        email_service = EmailNotificationService()
        sent_count = 0

        for user_id in user_ids:
            try:
                utilisateur = Utilisateur.objects.get(id=user_id)

                success = email_service.send_welcome_email(utilisateur)
                if success:
                    sent_count += 1

            except Utilisateur.DoesNotExist:
                logger.error(f"Utilisateur non trouvé: {user_id}")
            except Exception as e:
                logger.error(f"Erreur pour l'utilisateur {user_id}: {str(e)}")

        logger.info(f"{sent_count} emails de bienvenue envoyés sur {len(user_ids)} utilisateurs")
        return sent_count

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des emails de bienvenue: {str(e)}")
        raise


@shared_task
def cleanup_old_notifications_task(days_to_keep: int = 90):
    """
    Tâche pour nettoyer les anciennes notifications.

    Args:
        days_to_keep: Nombre de jours à conserver (défaut: 90)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Compter avant suppression
        count_before = Notification.objects.count()

        # Supprimer les notifications archivées ou lues de plus de X jours
        notifications_to_delete = Notification.objects.filter(
            Q(est_vue='ARCHIVEE') | Q(est_vue='VUE'),
            date_creation__lt=cutoff_date
        )

        deleted_count = notifications_to_delete.count()
        notifications_to_delete.delete()

        # Nettoyer les synthèses anciennes
        digests_to_delete = NotificationDigest.objects.filter(
            date_creation__lt=cutoff_date
        )
        digests_deleted = digests_to_delete.count()
        digests_to_delete.delete()

        # Désactiver les abonnements push inactifs depuis longtemps
        inactive_cutoff = timezone.now() - timedelta(days=30)
        inactive_subscriptions = PushSubscription.objects.filter(
            is_active=True,
            last_seen__lt=inactive_cutoff
        )

        for subscription in inactive_subscriptions:
            subscription.desactiver()

        count_after = Notification.objects.count()

        logger.info(
            f"Nettoyage terminé: "
            f"{deleted_count} notifications supprimées, "
            f"{digests_deleted} synthèses supprimées, "
            f"{inactive_subscriptions.count()} abonnements désactivés. "
            f"Total avant/après: {count_before}/{count_after}"
        )

        return {
            'notifications_deleted': deleted_count,
            'digests_deleted': digests_deleted,
            'subscriptions_deactivated': inactive_subscriptions.count(),
            'total_before': count_before,
            'total_after': count_after
        }

    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
        raise


@shared_task
def retry_failed_notifications_task():
    """
    Tâche pour réessayer l'envoi des notifications en échec.
    """
    try:
        # Notifications email en échec
        failed_emails = Notification.objects.filter(
            envoyee_email=True,
            email_statut='ECHEC',
            date_creation__gte=timezone.now() - timedelta(days=1)  # Seulement les dernières 24h
        )

        email_retry_count = 0
        for notification in failed_emails:
            try:
                send_notification_email_task.delay(str(notification.id))
                email_retry_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de la relance pour {notification.id}: {str(e)}")

        # Synthèses en échec
        failed_digests = NotificationDigest.objects.filter(
            statut='ECHEC',
            date_creation__gte=timezone.now() - timedelta(days=1)
        )

        digest_retry_count = 0
        for digest in failed_digests:
            try:
                notification_service = NotificationService()
                notification_service.send_digest_email(digest)
                digest_retry_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de la relance de la synthèse {digest.id}: {str(e)}")

        logger.info(
            f"Relance terminée: "
            f"{email_retry_count} emails relancés, "
            f"{digest_retry_count} synthèses relancées"
        )

        return {
            'emails_retried': email_retry_count,
            'digests_retried': digest_retry_count
        }

    except Exception as e:
        logger.error(f"Erreur lors de la relance: {str(e)}")
        raise


@shared_task
def check_push_subscriptions_health_task():
    """
    Tâche pour vérifier la santé des abonnements push.

    Vérifie les abonnements expirés ou invalides et les désactive.
    """
    try:
        notification_service = NotificationService()
        push_service = notification_service.push_service

        if not push_service:
            logger.warning("Service push non disponible")
            return 0

        # Récupérer tous les abonnements actifs
        active_subscriptions = PushSubscription.objects.filter(
            is_active=True
        )

        deactivated_count = 0

        for subscription in active_subscriptions:
            try:
                # Vérifier si l'abonnement est encore valide
                # (cette logique dépend du service push spécifique)
                is_valid = True

                if subscription.device_type == 'WEB' and push_service.webpush_service:
                    is_valid = push_service.webpush_service.validate_subscription(subscription)
                elif subscription.device_type in ['ANDROID', 'IOS'] and push_service.firebase_service:
                    is_valid = push_service.firebase_service.validate_subscription(subscription)

                if not is_valid:
                    subscription.desactiver()
                    deactivated_count += 1
                    logger.info(f"Abonnement désactivé: {subscription.device_id}")

            except Exception as e:
                logger.error(f"Erreur lors de la vérification de {subscription.device_id}: {str(e)}")
                continue

        logger.info(f"{deactivated_count} abonnements push désactivés")
        return deactivated_count

    except Exception as e:
        logger.error(f"Erreur lors de la vérification des abonnements: {str(e)}")
        raise


@shared_task
def notify_system_maintenance_task(
        maintenance_start: str,
        maintenance_end: str,
        reason: str
):
    """
    Tâche pour notifier d'une maintenance système.

    Args:
        maintenance_start: Date de début de maintenance (ISO format)
        maintenance_end: Date de fin de maintenance (ISO format)
        reason: Raison de la maintenance
    """
    try:
        notification_service = NotificationService()

        # Récupérer tous les utilisateurs
        users = Utilisateur.objects.filter(is_active=True)
        user_ids = [str(user.id) for user in users]

        # Préparer les métadonnées
        metadata = {
            'maintenance_start': maintenance_start,
            'maintenance_end': maintenance_end,
            'reason': reason,
            'notification_type': 'SYSTEM_MAINTENANCE'
        }

        # Créer la tâche d'envoi en masse
        send_bulk_notifications_task.delay(
            user_ids=user_ids,
            type_notification='SYSTEM_MAINTENANCE',
            titre="Maintenance système planifiée",
            message=f"Une maintenance système est planifiée du {maintenance_start} au {maintenance_end}. Raison: {reason}",
            metadata=metadata,
            envoyer_email=True,
            envoyer_push=True
        )

        logger.info(f"Notification de maintenance planifiée pour {len(user_ids)} utilisateurs")

    except Exception as e:
        logger.error(f"Erreur lors de la planification des notifications de maintenance: {str(e)}")
        raise