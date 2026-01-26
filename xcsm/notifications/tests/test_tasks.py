"""
Tests unitaires pour les tâches Celery de notifications.
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from xcsm.notifications.tasks import (
    send_notification_email_task,
    send_bulk_notifications_task,
    create_digests_for_users_task,
    send_welcome_emails_task,
    cleanup_old_notifications_task,
    retry_failed_notifications_task,
    check_push_subscriptions_health_task,
    notify_system_maintenance_task
)
from xcsm.notifications.models import (
    Notification,
    NotificationPreference,
    NotificationDigest,
    PushSubscription
)
from xcsm.models import Utilisateur


class NotificationTasksTest(TestCase):
    """
    Tests pour les tâches Celery du système de notifications.
    """

    def setUp(self):
        """
        Configuration des tests.
        """
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@xcsm.local',
            password='testpass123',
            type_compte='ENSEIGNANT'
        )

    @patch('xcsm.notifications.tasks.EmailNotificationService')
    def test_send_notification_email_task_success(self, mock_email_service_class):
        """
        Test de la tâche send_notification_email_task avec succès.
        """
        # Créer une notification
        notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test',
            message='Test message',
            envoyee_email=True
        )

        # Configurer le mock
        mock_service = mock_email_service_class.return_value
        mock_service.send_notification_email.return_value = True

        # Exécuter la tâche (directement sans Celery)
        send_notification_email_task(str(notification.id))

        # Vérifier l'appel au service
        mock_service.send_notification_email.assert_called_once_with(notification)

    @patch('xcsm.notifications.tasks.NotificationService')
    def test_send_bulk_notifications_task(self, mock_notification_service_class):
        """
        Test de la tâche send_bulk_notifications_task.
        """
        user_ids = [str(self.user.id)]
        
        # Configurer le mock
        mock_service = mock_notification_service_class.return_value
        mock_notification = MagicMock()
        mock_notification.id = 'notif-id-123'
        mock_notification.envoyee_email = False
        mock_service.create_notification.return_value = mock_notification

        # Exécuter
        count = send_bulk_notifications_task(
            user_ids=user_ids,
            type_notification='SYSTEM_ALERT',
            titre='Alert',
            message='System alert'
        )

        self.assertEqual(count, 1)
        mock_service.create_notification.assert_called_once()

    @patch('xcsm.notifications.tasks.NotificationService')
    def test_create_digests_for_users_task(self, mock_notification_service_class):
        """
        Test de la tâche create_digests_for_users_task.
        """
        # Mettre à jour la préférence pour la synthèse (déjà créée par signal)
        pref, _ = NotificationPreference.objects.get_or_create(utilisateur=self.user)
        pref.digest_frequency = 24
        pref.email_notifications_enabled = True
        pref.save()

        mock_service = mock_notification_service_class.return_value
        mock_service.create_digest_for_user.return_value = MagicMock()

        # Exécuter
        count = create_digests_for_users_task()

        self.assertEqual(count, 1)
        mock_service.create_digest_for_user.assert_called_once_with(self.user)

    @patch('xcsm.notifications.tasks.EmailNotificationService')
    def test_send_welcome_emails_task(self, mock_email_service_class):
        """
        Test de la tâche send_welcome_emails_task.
        """
        mock_service = mock_email_service_class.return_value
        mock_service.send_welcome_email.return_value = True

        # Exécuter
        count = send_welcome_emails_task([str(self.user.id)])

        self.assertEqual(count, 1)
        mock_service.send_welcome_email.assert_called_once_with(self.user)

    def test_cleanup_old_notifications_task(self):
        """
        Test de la tâche cleanup_old_notifications_task.
        """
        # Créer une ancienne notification (simulée via date_creation en db)
        old_date = timezone.now() - timedelta(days=100)
        
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = old_date
            Notification.objects.create(
                utilisateur=self.user,
                type_notification='AUTRE',
                titre='Old',
                message='Old message',
                est_vue='VUE'
            )
            
        # Vérifier qu'elle existe
        self.assertEqual(Notification.objects.count(), 1)

        # Exécuter le nettoyage (défaut 90 jours)
        result = cleanup_old_notifications_task(days_to_keep=90)

        self.assertEqual(result['notifications_deleted'], 1)
        self.assertEqual(Notification.objects.count(), 0)

    @patch('xcsm.notifications.tasks.send_notification_email_task.delay')
    def test_retry_failed_notifications_task(self, mock_relay_task):
        """
        Test de la tâche retry_failed_notifications_task.
        """
        from xcsm.notifications.signals import process_notification_channels
        from django.db.models.signals import post_save
        from xcsm.notifications.models import Notification

        # Déconnecter temporairement le signal pour éviter l'appel immédiat à delay lors de la création
        post_save.disconnect(process_notification_channels, sender=Notification)
        
        try:
            # Créer une notification en échec
            Notification.objects.create(
                utilisateur=self.user,
                type_notification='DOCUMENT_TRAITE',
                titre='Failed',
                message='Failed message',
                envoyee_email=True,
                email_statut='ECHEC'
            )

            # Exécuter
            result = retry_failed_notifications_task()

            self.assertEqual(result['emails_retried'], 1)
            # Maintenant il ne devrait y avoir qu'un seul appel (depuis la tâche de retry)
            mock_relay_task.assert_called_once()
        finally:
            # Reconnecter le signal
            post_save.connect(process_notification_channels, sender=Notification)

    @patch('xcsm.notifications.tasks.NotificationService')
    def test_check_push_subscriptions_health_task(self, mock_notification_service_class):
        """
        Test de la tâche check_push_subscriptions_health_task.
        """
        # Créer un abonnement
        sub = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='device-123',
            subscription_data={},
            is_active=True
        )

        # Configurer le mock
        mock_service = mock_notification_service_class.return_value
        mock_push = MagicMock()
        mock_webpush = MagicMock()
        mock_push.webpush_service = mock_webpush
        mock_service.push_service = mock_push
        
        # Simuler une validation échouée
        mock_webpush.validate_subscription.return_value = False

        # Exécuter
        count = check_push_subscriptions_health_task()

        self.assertEqual(count, 1)
        sub.refresh_from_db()
        self.assertFalse(sub.is_active)

    @patch('xcsm.notifications.tasks.send_bulk_notifications_task')
    def test_notify_system_maintenance_task(self, mock_bulk_task):
        """
        Test de la tâche notify_system_maintenance_task.
        """
        start = timezone.now().isoformat()
        end = (timezone.now() + timedelta(hours=2)).isoformat()
        
        # Exécuter
        notify_system_maintenance_task(start, end, "Reason")

        # Vérifier que la tâche de masse a été appelée
        mock_bulk_task.delay.assert_called_once()
        args, kwargs = mock_bulk_task.delay.call_args
        self.assertEqual(kwargs['type_notification'], 'SYSTEM_MAINTENANCE')
        self.assertIn("Reason", kwargs['message'])
