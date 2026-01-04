"""
Signaux Django pour le système de notifications XCSM.

Ce module contient les signaux qui déclenchent automatiquement
des notifications en réponse à des événements du système.
"""
import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Notification, NotificationPreference
from .services import NotificationService
from xcsm.models import (
    Utilisateur,
    FichierSource,
    Enseignant,
    Etudiant,
    Administrateur
)

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNAL POUR LES UTILISATEURS
# ============================================================================

@receiver(post_save, sender=Utilisateur)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    """
    Crée automatiquement les préférences de notification pour un nouvel utilisateur.

    Ce signal est déclenché après la création d'un nouvel utilisateur.
    """
    if created:
        try:
            # Créer les préférences par défaut
            NotificationPreference.objects.create(utilisateur=instance)
            logger.info(f"Préférences de notification créées pour {instance.username}")

            # Envoyer un email de bienvenue (asynchrone)
            from .tasks import send_welcome_emails_task
            send_welcome_emails_task.delay([str(instance.id)])

        except Exception as e:
            logger.error(f"Erreur lors de la création des préférences: {str(e)}")


@receiver(post_save, sender=Enseignant)
@receiver(post_save, sender=Etudiant)
@receiver(post_save, sender=Administrateur)
def notify_profile_updated(sender, instance, created, **kwargs):
    """
    Notifie lorsqu'un profil est mis à jour.

    Ce signal est déclenché après la mise à jour d'un profil.
    """
    if not created:  # Seulement pour les mises à jour, pas la création
        try:
            notification_service = NotificationService()

            notification_service.create_notification_from_template(
                utilisateur=instance.utilisateur,
                template_code='PROFIL_MIS_A_JOUR',
                context={
                    'profile_type': sender.__name__,
                    'date_mise_a_jour': timezone.now().isoformat(),
                    'user_full_name': instance.utilisateur.get_full_name()
                }
            )

            logger.info(f"Notification de profil mis à jour pour {instance.utilisateur.username}")

        except Exception as e:
            logger.error(f"Erreur lors de la notification de profil: {str(e)}")


# ============================================================================
# SIGNAL POUR LES DOCUMENTS
# ============================================================================

@receiver(post_save, sender=FichierSource)
def notify_document_status_change(sender, instance, created, **kwargs):
    """
    Notifie les changements de statut des documents.

    Ce signal est déclenché après la création ou la mise à jour d'un document.
    """
    if not created and 'statut_traitement' in kwargs.get('update_fields', []):
        try:
            notification_service = NotificationService()

            # Récupérer l'utilisateur (l'enseignant propriétaire)
            utilisateur = instance.enseignant.utilisateur

            if instance.statut_traitement == 'TRAITE':
                # Document traité avec succès
                notification_service.notify_document_processed(
                    utilisateur=utilisateur,
                    fichier_source=instance,
                    success=True,
                    message="Votre document a été traité avec succès et est maintenant disponible.",
                    details={
                        'document_id': str(instance.id),
                        'document_titre': instance.titre,
                        'mongo_id': instance.mongo_transforme_id,
                        'processing_time': 'N/A'  # À compléter avec les logs de traitement
                    }
                )

            elif instance.statut_traitement == 'ERREUR':
                # Erreur lors du traitement
                notification_service.notify_document_processed(
                    utilisateur=utilisateur,
                    fichier_source=instance,
                    success=False,
                    message="Une erreur est survenue lors du traitement de votre document.",
                    details={
                        'document_id': str(instance.id),
                        'document_titre': instance.titre,
                        'error_type': 'processing_error'
                    }
                )

            logger.info(f"Notification de statut de document pour {instance.titre}")

        except Exception as e:
            logger.error(f"Erreur lors de la notification de document: {str(e)}")


# ============================================================================
# SIGNAL POUR LES NOTIFICATIONS
# ============================================================================

@receiver(pre_save, sender=Notification)
def set_notification_dates(sender, instance, **kwargs):
    """
    Définit automatiquement les dates des notifications.

    Ce signal est déclenché avant la sauvegarde d'une notification.
    """
    if not instance.pk:  # Nouvelle notification
        instance.date_creation = timezone.now()

        # Si la notification est envoyée immédiatement, définir date_envoi
        if instance.envoyee_email or instance.envoyee_push:
            instance.date_envoi = timezone.now()


@receiver(post_save, sender=Notification)
def process_notification_channels(sender, instance, created, **kwargs):
    """
    Traite les canaux de notification après la création.

    Ce signal est déclenché après la création d'une notification.
    """
    if created:
        try:
            from .tasks import send_notification_email_task

            # Envoyer l'email de manière asynchrone si demandé
            if instance.envoyee_email and instance.envoyee_in_app:
                send_notification_email_task.delay(str(instance.id))

                logger.info(f"Tâche d'email planifiée pour la notification {instance.id}")

            # Les notifications push sont gérées par le service directement
            # car elles nécessitent des abonnements spécifiques

        except Exception as e:
            logger.error(f"Erreur lors du traitement des canaux: {str(e)}")


# ============================================================================
# SIGNAL POUR LE SYSTÈME
# ============================================================================

@receiver(post_delete, sender=Utilisateur)
def cleanup_user_notifications(sender, instance, **kwargs):
    """
    Nettoie les notifications lors de la suppression d'un utilisateur.

    Ce signal est déclenché après la suppression d'un utilisateur.
    """
    try:
        # Supprimer toutes les notifications de l'utilisateur
        Notification.objects.filter(utilisateur=instance).delete()

        # Supprimer les préférences
        NotificationPreference.objects.filter(utilisateur=instance).delete()

        # Supprimer les abonnements push
        from .models import PushSubscription
        PushSubscription.objects.filter(utilisateur=instance).delete()

        # Supprimer les synthèses
        from .models import NotificationDigest
        NotificationDigest.objects.filter(utilisateur=instance).delete()

        logger.info(f"Notifications nettoyées pour l'utilisateur supprimé: {instance.username}")

    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des notifications: {str(e)}")


@receiver(post_save, sender=NotificationPreference)
def log_preference_change(sender, instance, created, **kwargs):
    """
    Log les changements de préférences de notification.

    Ce signal est déclenché après la modification des préférences.
    """
    if not created:
        logger.info(f"Préférences de notification mises à jour pour {instance.utilisateur.username}")

        # Si les emails sont désactivés, annuler les synthèses en attente
        if not instance.email_notifications_enabled:
            from .models import NotificationDigest
            pending_digests = NotificationDigest.objects.filter(
                utilisateur=instance.utilisateur,
                statut='EN_ATTENTE'
            )

            for digest in pending_digests:
                digest.statut = 'ANNULÉ'
                digest.save()
                logger.info(f"Synthèse {digest.id} annulée - emails désactivés")


# ============================================================================
# FONCTIONS D'ENREGISTREMENT DES SIGNAUX
# ============================================================================

def register_notification_signals():
    """
    Enregistre tous les signaux pour le système de notifications.

    Cette fonction doit être appelée dans la configuration de l'application.
    """
    # Les signaux sont automatiquement enregistrés via les décorateurs @receiver
    # Cette fonction permet de s'assurer que tous les signaux sont chargés
    logger.info("Signaux de notifications enregistrés")

    return [
        create_user_notification_preferences,
        notify_profile_updated,
        notify_document_status_change,
        set_notification_dates,
        process_notification_channels,
        cleanup_user_notifications,
        log_preference_change
    ]