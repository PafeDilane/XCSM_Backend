"""
Tâches Celery pour le système de notifications XCSM.

Ce module gère l'exécution asynchrone des communications :
- Envoi différé des emails pour ne pas bloquer l'API.
- Traitement de masse (notifications système ou maintenance).
- Génération périodique des synthèses (Digests) pour éviter le spam.
- Maintenance automatique (nettoyage des anciennes données).
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
    Tâche spécifique pour l'envoi d'un mail de notification individuel.
    Réessaie automatiquement 3 fois en cas d'erreur SMTP temporaire.
    """
    try:
        # Récupération de l'objet métier
        notification = Notification.objects.get(id=notification_id)

        # Délégation au service d'envoi d'emails
        email_service = EmailNotificationService()
        success = email_service.send_notification_email(notification)

        if not success:
            raise Exception("Le service d'email a retourné un échec")

        logger.info(f"Email envoyé avec succès: {notification_id}")

    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} introuvable.")
    except Exception as e:
        logger.error(f"Erreur d'envoi email ({notification_id}): {str(e)}")
        # Déclenche un nouvel essai via Celery
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
    Tâche lourde pour diffuser un message à une liste d'utilisateurs.
    Utile pour les alertes système ou les messages administratifs.
    """
    try:
        notification_service = NotificationService()
        created_count = 0

        for user_id in user_ids:
            try:
                utilisateur = Utilisateur.objects.get(id=user_id)

                # Création de l'entrée in-app
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
                    # Si un mail est demandé, on délègue à la tâche atomique pour isolation
                    if envoyer_email and notification.envoyee_email:
                        send_notification_email_task.delay(str(notification.id))

            except Exception as e:
                logger.error(f"Échec pour l'utilisateur {user_id}: {str(e)}")
                continue

        logger.info(f"Diffusion terminée: {created_count} messages générés.")
        return created_count

    except Exception as e:
        logger.error(f"Erreur fatale lors de la diffusion de masse: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def create_digests_for_users_task():
    """
    Moteur de synthèse périodique. 
    Parcourt les utilisateurs ayant activé l'option 'Digest' et génère un rapport email.
    """
    try:
        notification_service = NotificationService()
        created_count = 0

        # Filtre les utilisateurs ayant une fréquence de synthèse définie (> 0 heures)
        preferences = NotificationPreference.objects.filter(
            digest_frequency__gt=0,
            email_notifications_enabled=True
        ).select_related('utilisateur')

        for preference in preferences:
            try:
                # Calcul de l'échéance selon la dernière synthèse envoyée
                last_digest = NotificationDigest.objects.filter(
                    utilisateur=preference.utilisateur
                ).order_by('-date_creation').first()

                if last_digest:
                    next_run = last_digest.date_creation + timedelta(hours=preference.digest_frequency)
                    if timezone.now() < next_run:
                        continue # Trop tôt pour cet utilisateur

                # Génération et envoi de la synthèse
                digest = notification_service.create_digest_for_user(preference.utilisateur)
                if digest:
                    notification_service.send_digest_email(digest)
                    created_count += 1

            except Exception as e:
                logger.error(f"Erreur de synthèse pour {preference.utilisateur}: {str(e)}")
                continue

        return created_count

    except Exception as e:
        logger.error(f"Erreur globale lors de la création des synthèses: {str(e)}")
        raise


@shared_task
def send_welcome_emails_task(user_ids: List[str]):
    """
    Envoi asynchrone des emails de bienvenue après inscription.
    """
    try:
        email_service = EmailNotificationService()
        sent_count = 0

        for user_id in user_ids:
            try:
                utilisateur = Utilisateur.objects.get(id=user_id)
                if email_service.send_welcome_email(utilisateur):
                    sent_count += 1
            except Exception:
                continue

        return sent_count
    except Exception as e:
        logger.error(f"Erreur bienvenue: {str(e)}")
        raise


@shared_task
def cleanup_old_notifications_task(days_to_keep: int = 90):
    """
    Tâche d'hygiène de la base de données.
    Supprime les anciennes notifications (lues ou archivées) pour libérer de l'espace MySQL.
    Désactive également les tokens push inactifs.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Suppression MySQL
        notifications_to_delete = Notification.objects.filter(
            Q(est_vue='ARCHIVEE') | Q(est_vue='VUE'),
            date_creation__lt=cutoff_date
        )
        deleted_count = notifications_to_delete.count()
        notifications_to_delete.delete()

        # Invalidation des abonnements Push inactifs (30 jours sans nouvelles)
        inactive_cutoff = timezone.now() - timedelta(days=30)
        PushSubscription.objects.filter(is_active=True, last_seen__lt=inactive_cutoff).update(is_active=False)

        logger.info(f"Nettoyage effectué: {deleted_count} notifications supprimées.")
        return deleted_count

    except Exception as e:
        logger.error(f"Erreur de nettoyage: {str(e)}")
        raise


@shared_task
def retry_failed_notifications_task():
    """
    Tâche de rattrapage.
    Tente de renvoyer les notifications qui ont échoué au cours des dernières 24h.
    """
    try:
        # Reprise des emails en erreur
        failed_emails = Notification.objects.filter(
            envoyee_email=True,
            email_statut='ECHEC',
            date_creation__gte=timezone.now() - timedelta(days=1)
        )

        for notification in failed_emails:
            send_notification_email_task.delay(str(notification.id))

        return failed_emails.count()
    except Exception as e:
        logger.error(f"Erreur de rattrapage: {str(e)}")
        raise


@shared_task
def notify_system_maintenance_task(maintenance_start: str, maintenance_end: str, reason: str):
    """
    Déclencheur d'alerte de maintenance.
    Envoie un message in-app, push et email à tous les utilisateurs actifs.
    """
    try:
        users = Utilisateur.objects.filter(is_active=True)
        user_ids = [str(user.id) for user in users]

        # Planification du job de masse
        send_bulk_notifications_task.delay(
            user_ids=user_ids,
            type_notification='SYSTEM_MAINTENANCE',
            titre="🚧 Maintenance Système Planifiée",
            message=f"La plateforme XCSM sera indisponible de {maintenance_start} à {maintenance_end}. Motif: {reason}",
            metadata={'start': maintenance_start, 'end': maintenance_end},
            envoyer_email=True,
            envoyer_push=True
        )
        return len(user_ids)
    except Exception as e:
        logger.error(f"Échec planification maintenance: {str(e)}")
        raise