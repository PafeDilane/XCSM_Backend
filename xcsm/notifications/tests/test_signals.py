"""
Tests unitaires pour les signaux Django de notifications.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from xcsm.notifications.models import (
    Notification,
    NotificationPreference,
    PushSubscription,
    NotificationDigest
)
from xcsm.models import Utilisateur, FichierSource, Enseignant
from xcsm.notifications.signals import (
    create_user_notification_preferences,
    notify_profile_updated,
    notify_document_status_change,
    set_notification_dates,
    process_notification_channels,
    cleanup_user_notifications,
    log_preference_change
)


class NotificationSignalsTest(TestCase):
    """
    Tests pour les signaux du système de notifications.
    """

    @patch('xcsm.notifications.tasks.send_welcome_emails_task.delay')
    def test_create_user_notification_preferences_signal(self, mock_welcome_task):
        """
        Test du signal create_user_notification_preferences.
        """
        # Créer un utilisateur déclenche le signal
        user = Utilisateur.objects.create_user(
            username='newuser',
            email='new@xcsm.local',
            password='password123'
        )

        # Vérifier que les préférences ont été créées
        self.assertTrue(NotificationPreference.objects.filter(utilisateur=user).exists())
        
        # Vérifier que la tâche d'email de bienvenue a été planifiée
        mock_welcome_task.assert_called_once_with([str(user.id)])

    @patch('xcsm.notifications.services.NotificationService.create_notification_from_template')
    def test_notify_profile_updated_signal(self, mock_create_notif):
        """
        Test du signal notify_profile_updated.
        """
        user = Utilisateur.objects.create_user(
            username='teacher',
            email='teacher@xcsm.local',
            password='password123',
            type_compte='ENSEIGNANT'
        )
        
        # Créer le profil enseignant manuellement car il n'est pas créé automatiquement
        enseignant = Enseignant.objects.create(
            utilisateur=user,
            specialite='Informatique',
            departement='Sciences'
        )
        
        # Le signal est déclenché par post_save sur Enseignant
        enseignant.grade = 'Professeur'
        enseignant.save()

        # Vérifier l'appel au service de notification
        mock_create_notif.assert_called_once()
        args, kwargs = mock_create_notif.call_args
        self.assertEqual(kwargs['template_code'], 'PROFIL_MIS_A_JOUR')
        self.assertEqual(kwargs['utilisateur'], user)

    @patch('xcsm.notifications.services.NotificationService.notify_document_processed')
    def test_notify_document_status_change_signal(self, mock_notify_processed):
        """
        Test du signal notify_document_status_change.
        """
        user = Utilisateur.objects.create_user(
            username='teacher_doc',
            email='doc@xcsm.local',
            password='password123',
            type_compte='ENSEIGNANT'
        )
        
        # Créer le profil enseignant
        enseignant = Enseignant.objects.create(
            utilisateur=user,
            specialite='Informatique',
            departement='Sciences'
        )
        
        doc = FichierSource.objects.create(
            titre='Test Doc',
            enseignant=enseignant,
            fichier_original='test.pdf',
            statut_traitement='CHARGEMENT'
        )
        
        # Changer le statut
        doc.statut_traitement = 'TRAITE'
        doc.save(update_fields=['statut_traitement'])

        # Vérifier l'appel au service
        mock_notify_processed.assert_called_once()
        args, kwargs = mock_notify_processed.call_args
        self.assertEqual(kwargs['utilisateur'], user)
        self.assertEqual(kwargs['success'], True)

    def test_set_notification_dates_signal(self):
        """
        Test du signal set_notification_dates (pre_save).
        """
        user = Utilisateur.objects.create_user(
            username='user_notif',
            email='notif@xcsm.local',
            password='password123'
        )
        
        notif = Notification(
            utilisateur=user,
            type_notification='AUTRE',
            titre='Test',
            message='Msg'
        )
        
        # Avant sauvegarde, pas de date
        self.assertIsNone(notif.date_creation)
        
        notif.save()
        
        # Après sauvegarde, date_creation définie
        self.assertIsNotNone(notif.date_creation)

    @patch('xcsm.notifications.tasks.send_notification_email_task.delay')
    def test_process_notification_channels_signal(self, mock_email_task):
        """
        Test du signal process_notification_channels (post_save).
        """
        user = Utilisateur.objects.create_user(
            username='user_notif_channels',
            email='channels@xcsm.local',
            password='password123'
        )
        
        notif = Notification.objects.create(
            utilisateur=user,
            type_notification='AUTRE',
            titre='Test Email',
            message='Msg',
            envoyee_email=True,
            envoyee_in_app=True
        )
        
        # Vérifier que la tâche d'email a été lancée
        mock_email_task.assert_called_once_with(str(notif.id))

    def test_cleanup_user_notifications_signal(self):
        """
        Test du signal cleanup_user_notifications (post_delete).
        """
        user = Utilisateur.objects.create_user(
            username='user_to_delete',
            email='delete@xcsm.local',
            password='password123'
        )
        
        # Créer des données liées
        notif = Notification.objects.create(
            utilisateur=user,
            type_notification='AUTRE',
            titre='To Delete',
            message='Msg'
        )
        
        user_id = user.id
        
        # Supprimer l'utilisateur
        user.delete()
        
        # Vérifier que les données sont supprimées
        self.assertFalse(Notification.objects.filter(id=notif.id).exists())
        self.assertFalse(NotificationPreference.objects.filter(utilisateur_id=user_id).exists())

    def test_log_preference_change_signal(self):
        """
        Test du signal log_preference_change.
        """
        user = Utilisateur.objects.create_user(
            username='user_pref_change',
            email='pref@xcsm.local',
            password='password123'
        )
        
        pref = NotificationPreference.objects.get(utilisateur=user)
        
        # Créer une synthèse en attente
        digest = NotificationDigest.objects.create(
            utilisateur=user,
            contenu_html='<p>Test</p>',
            contenu_text='Test',
            statut='EN_ATTENTE'
        )
        
        # Désactiver les notifications email
        pref.email_notifications_enabled = False
        pref.save()
        
        # Vérifier que la synthèse a été annulée
        digest.refresh_from_db()
        self.assertEqual(digest.statut, 'ANNULÉ')
