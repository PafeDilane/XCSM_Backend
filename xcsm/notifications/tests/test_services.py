"""
Tests unitaires pour les services de notifications.
"""
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone
from django.core import mail

from xcsm.notifications.services import (
    NotificationService,
    EmailNotificationService,
    PushNotificationService
)
from xcsm.notifications.models import (
    Notification,
    NotificationPreference,
    PushSubscription,
    NotificationDigest
)
from xcsm.models import Utilisateur, FichierSource, Cours


class NotificationServiceTest(TestCase):
    """
    Tests pour le service NotificationService.
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

        self.service = NotificationService()

        # Mock des services dépendants
        self.service.email_service = Mock()
        self.service.push_service = Mock()

    def test_create_notification_basic(self):
        """
        Test de création basique d'une notification.
        """
        notification = self.service.create_notification(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test Notification',
            message='This is a test notification',
            metadata={'test': 'value'}
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.utilisateur, self.user)
        self.assertEqual(notification.type_notification, 'DOCUMENT_TRAITE')
        self.assertEqual(notification.titre, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertEqual(notification.metadata, {'test': 'value'})
        self.assertTrue(notification.envoyee_in_app)

    @patch.object(NotificationService, '_get_user_preferences')
    def test_create_notification_with_preferences(self, mock_get_prefs):
        """
        Test de création avec préférences utilisateur.
        """
        # Créer un mock des préférences
        mock_pref = Mock()
        mock_pref.get_preference_for_type.return_value = False  # Désactiver tous les canaux
        mock_get_prefs.return_value = mock_pref

        notification = self.service.create_notification(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test',
            message='Test',
            envoyer_email=True,
            envoyer_push=True,
            envoyer_in_app=True
        )

        # Vérifier que les canaux ont été désactivés selon les préférences
        self.assertFalse(notification.envoyee_email)
        self.assertFalse(notification.envoyee_push)
        self.assertFalse(notification.envoyee_in_app)

        # Vérifier que les services n'ont pas été appelés
        self.service.email_service.send_notification_email.assert_not_called()
        self.service.push_service.send_push_notification.assert_not_called()

    @patch('xcsm.notifications.services.NotificationTemplate')
    def test_create_notification_from_template(self, mock_template_model):
        """
        Test de création depuis un template.
        """
        # Mock du template
        mock_template = Mock()
        mock_template.render_email.return_value = (
            'Email Subject',
            '<p>Email HTML</p>',
            'Email Text'
        )
        mock_template.render_push.return_value = ('Push Title', 'Push Message')
        mock_template.render_in_app.return_value = ('In-App Title', 'In-App Message')
        mock_template.type_notification = 'DOCUMENT_TRAITE'

        mock_template_model.objects.filter.return_value.first.return_value = mock_template

        # Mock de la méthode create_notification
        with patch.object(self.service, 'create_notification') as mock_create:
            mock_notification = Mock()
            mock_create.return_value = mock_notification

            # Appeler la méthode
            result = self.service.create_notification_from_template(
                utilisateur=self.user,
                template_code='TEST_TEMPLATE',
                context={'name': 'Test'}
            )

            # Vérifier les appels
            mock_template_model.objects.filter.assert_called_with(
                code='TEST_TEMPLATE',
                is_active=True
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]

            self.assertEqual(call_kwargs['utilisateur'], self.user)
            self.assertEqual(call_kwargs['type_notification'], 'DOCUMENT_TRAITE')
            self.assertEqual(call_kwargs['titre'], 'In-App Title')
            self.assertEqual(call_kwargs['message'], 'In-App Message')
            self.assertEqual(call_kwargs['metadata'], {'name': 'Test'})

            self.assertEqual(result, mock_notification)

    def test_notify_document_processed_success(self):
        """
        Test de notification de document traité avec succès.
        """
        # Créer un fichier source de test
        fichier_source = FichierSource.objects.create(
            titre='Test Document',
            enseignant=self.user.profil_enseignant,
            fichier_original='test.pdf'
        )

        # Mock de la méthode create_notification_from_template
        with patch.object(self.service, 'create_notification_from_template') as mock_create:
            mock_notification = Mock()
            mock_create.return_value = mock_notification

            # Appeler la méthode
            notifications = self.service.notify_document_processed(
                utilisateur=self.user,
                fichier_source=fichier_source,
                success=True,
                message='Document traité avec succès',
                details={'pages': 25, 'granules': 150}
            )

            # Vérifier l'appel
            mock_create.assert_called_once()

            call_kwargs = mock_create.call_args[1]
            self.assertEqual(call_kwargs['template_code'], 'DOCUMENT_TRAITE_SUCCESS')
            self.assertEqual(call_kwargs['utilisateur'], self.user)
            self.assertEqual(call_kwargs['fichier_source'], fichier_source)

            context = call_kwargs['context']
            self.assertEqual(context['document_titre'], 'Test Document')
            self.assertEqual(context['document_id'], str(fichier_source.id))
            self.assertEqual(context['message'], 'Document traité avec succès')
            self.assertEqual(context['details'], {'pages': 25, 'granules': 150})

            self.assertEqual(len(notifications), 1)
            self.assertEqual(notifications[0], mock_notification)

    def test_create_digest_for_user(self):
        """
        Test de création de synthèse pour un utilisateur.
        """
        # Créer des notifications pour l'utilisateur
        for i in range(3):
            Notification.objects.create(
                utilisateur=self.user,
                type_notification='DOCUMENT_TRAITE',
                titre=f'Notification {i}',
                message=f'Message {i}'
            )

        # Créer une synthèse
        with patch('xcsm.notifications.services.render_to_string') as mock_render:
            mock_render.return_value = 'Rendered content'

            digest = self.service.create_digest_for_user(self.user)

        self.assertIsNotNone(digest)
        self.assertEqual(digest.utilisateur, self.user)
        self.assertEqual(digest.notifications.count(), 3)
        self.assertEqual(digest.contenu_html, 'Rendered content')
        self.assertEqual(digest.contenu_text, 'Rendered content')

    def test_create_digest_no_new_notifications(self):
        """
        Test de création de synthèse sans nouvelles notifications.
        """
        digest = self.service.create_digest_for_user(self.user)

        self.assertIsNone(digest)


class EmailNotificationServiceTest(TestCase):
    """
    Tests pour le service EmailNotificationService.
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

        self.fichier_source = FichierSource.objects.create(
            titre='Test Document',
            enseignant=self.user.profil_enseignant,
            fichier_original='test.pdf'
        )

        self.notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test Notification',
            message='This is a test notification',
            fichier_source=self.fichier_source,
            envoyee_email=True
        )

        self.service = EmailNotificationService()

    def test_send_notification_email_success(self):
        """
        Test d'envoi réussi d'un email de notification.
        """
        with patch('xcsm.notifications.services.render_to_string') as mock_render:
            mock_render.return_value = '<p>Email content</p>'

            success = self.service.send_notification_email(self.notification)

        self.assertTrue(success)

        # Vérifier que l'email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(email.to, ['test@xcsm.local'])
        self.assertIn('[XCSM] Test Notification', email.subject)
        self.assertIn('Email content', email.alternatives[0][0])

    def test_send_notification_email_no_email_channel(self):
        """
        Test d'envoi d'email lorsque le canal email est désactivé.
        """
        self.notification.envoyee_email = False

        success = self.service.send_notification_email(self.notification)

        self.assertFalse(success)
        self.assertEqual(len(mail.outbox), 0)

    @patch('xcsm.notifications.services.render_to_string')
    def test_send_notification_email_template_fallback(self, mock_render):
        """
        Test de fallback sur le template par défaut.
        """
        # Faire échouer le rendu du template spécifique
        mock_render.side_effect = [
            Exception('Template not found'),  # Premier appel échoue
            '<p>Default template</p>',        # Fallback réussi
            'Default text'                    # Template texte
        ]

        success = self.service.send_notification_email(self.notification)

        self.assertTrue(success)
        self.assertEqual(mock_render.call_count, 3)

    def test_send_digest_email(self):
        """
        Test d'envoi d'email de synthèse.
        """
        # Créer une synthèse
        digest = NotificationDigest.objects.create(
            utilisateur=self.user,
            contenu_html='<p>Digest HTML</p>',
            contenu_text='Digest text'
        )

        success = self.service.send_digest_email(digest)

        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['test@xcsm.local'])
        self.assertIn('[XCSM] Synthèse de vos notifications', email.subject)
        self.assertIn('Digest HTML', email.alternatives[0][0])

    def test_send_welcome_email(self):
        """
        Test d'envoi d'email de bienvenue.
        """
        success = self.service.send_welcome_email(self.user)

        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['test@xcsm.local'])
        self.assertEqual(email.subject, 'Bienvenue sur XCSM !')


class PushNotificationServiceTest(TestCase):
    """
    Tests pour le service PushNotificationService.
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

        self.notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test Notification',
            message='This is a test notification',
            envoyee_push=True
        )

        # Mock des services Firebase et WebPush
        self.firebase_mock = Mock()
        self.webpush_mock = Mock()

        self.service = PushNotificationService()
        self.service.firebase_service = self.firebase_mock
        self.service.webpush_service = self.webpush_mock

    def test_send_push_notification_web(self):
        """
        Test d'envoi de notification push web.
        """
        # Créer un abonnement web
        subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='web-device-123',
            subscription_data={'endpoint': 'https://example.com', 'keys': {'p256dh': 'test', 'auth': 'test'}}
        )

        # Configurer le mock
        self.webpush_mock.send_notification.return_value = True

        success = self.service.send_push_notification(self.notification)

        self.assertTrue(success)
        self.webpush_mock.send_notification.assert_called_once_with(subscription, self.notification)

    def test_send_push_notification_mobile(self):
        """
        Test d'envoi de notification push mobile.
        """
        # Créer un abonnement mobile
        subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='ANDROID',
            device_id='android-device-123',
            subscription_data={'token': 'firebase-token-123'}
        )

        # Configurer le mock
        self.firebase_mock.send_notification.return_value = True

        success = self.service.send_push_notification(self.notification)

        self.assertTrue(success)
        self.firebase_mock.send_notification.assert_called_once_with(subscription, self.notification)

    def test_send_push_no_subscriptions(self):
        """
        Test d'envoi sans abonnements.
        """
        success = self.service.send_push_notification(self.notification)

        self.assertFalse(success)
        self.webpush_mock.send_notification.assert_not_called()
        self.firebase_mock.send_notification.assert_not_called()

    def test_subscribe_device_new(self):
        """
        Test d'abonnement d'un nouvel appareil.
        """
        subscription_data = {
            'endpoint': 'https://example.com',
            'keys': {'p256dh': 'test', 'auth': 'test'}
        }

        success = self.service.subscribe_device(
            utilisateur=self.user,
            device_type='WEB',
            device_id='new-device-123',
            subscription_data=subscription_data,
            device_name='Test Browser',
            device_model='Chrome 120'
        )

        self.assertTrue(success)

        # Vérifier la création
        subscription = PushSubscription.objects.get(device_id='new-device-123')
        self.assertEqual(subscription.utilisateur, self.user)
        self.assertEqual(subscription.device_type, 'WEB')
        self.assertEqual(subscription.subscription_data, subscription_data)
        self.assertTrue(subscription.is_active)

    def test_subscribe_device_update_existing(self):
        """
        Test de mise à jour d'un appareil existant.
        """
        # Créer un abonnement existant
        existing = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='existing-device-123',
            subscription_data={'old': 'data'},
            is_active=False  # Désactivé
        )

        new_data = {
            'endpoint': 'https://example.com',
            'keys': {'p256dh': 'new', 'auth': 'new'}
        }

        success = self.service.subscribe_device(
            utilisateur=self.user,
            device_type='WEB',
            device_id='existing-device-123',
            subscription_data=new_data,
            device_name='Updated Browser',
            device_model='Chrome 121'
        )

        self.assertTrue(success)

        # Rafraîchir depuis la base de données
        existing.refresh_from_db()

        self.assertEqual(existing.subscription_data, new_data)
        self.assertEqual(existing.device_name, 'Updated Browser')
        self.assertEqual(existing.device_model, 'Chrome 121')
        self.assertTrue(existing.is_active)  # Doit être réactivé

    def test_unsubscribe_device(self):
        """
        Test de désabonnement d'un appareil.
        """
        # Créer un abonnement
        subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='device-to-unsubscribe',
            subscription_data={},
            is_active=True
        )

        success = self.service.unsubscribe_device(self.user, 'device-to-unsubscribe')

        self.assertTrue(success)

        # Rafraîchir depuis la base de données
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)
        self.assertIsNotNone(subscription.date_desactivation)

    def test_unsubscribe_nonexistent_device(self):
        """
        Test de désabonnement d'un appareil inexistant.
        """
        success = self.service.unsubscribe_device(self.user, 'non-existent-device')

        self.assertFalse(success)


class IntegrationTest(TestCase):
    """
    Tests d'intégration des services.
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

        self.service = NotificationService()

        # Remplacer les services par des mocks
        self.email_mock = Mock()
        self.push_mock = Mock()

        self.service.email_service = self.email_mock
        self.service.push_service = self.push_mock

    def test_full_notification_flow(self):
        """
        Test du flux complet de notification.
        """
        # Créer une notification via le service
        notification = self.service.create_notification(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test Notification',
            message='Test message',
            envoyer_email=True,
            envoyer_push=False,
            envoyer_in_app=True
        )

        # Vérifier la création
        self.assertIsNotNone(notification)

        # Vérifier que les services ont été appelés
        self.email_mock.send_notification_email.assert_called_once_with(notification)
        self.push_mock.send_push_notification.assert_not_called()

    def test_notify_multiple_users(self):
        """
        Test de notification de plusieurs utilisateurs.
        """
        # Créer un deuxième utilisateur
        user2 = Utilisateur.objects.create_user(
            username='testuser2',
            email='test2@xcsm.local',
            password='testpass123',
            type_compte='ETUDIANT'
        )

        # Créer un cours
        cours = Cours.objects.create(
            titre='Test Course',
            code='TEST-101',
            enseignant=self.user.profil_enseignant
        )

        # Mock de la méthode create_notification_from_template
        with patch.object(self.service, 'create_notification_from_template') as mock_create:
            mock_notification = Mock()
            mock_create.return_value = mock_notification

            # Notifier d'une nouvelle évaluation
            notifications = self.service.notify_new_evaluation(
                cours=cours,
                evaluation_titre='Test Evaluation',
                date_limite=timezone.now() + timedelta(days=7)
            )

            # Vérifier que create_notification_from_template a été appelé
            # (au moins pour les deux utilisateurs)
            self.assertGreaterEqual(mock_create.call_count, 2)

            # Vérifier les arguments
            for call in mock_create.call_args_list:
                kwargs = call[1]
                self.assertEqual(kwargs['template_code'], 'NOUVELLE_EVALUATION')
                self.assertEqual(kwargs['cours'], cours)

                context = kwargs['context']
                self.assertEqual(context['cours_titre'], 'Test Course')
                self.assertEqual(context['cours_code'], 'TEST-101')
                self.assertEqual(context['evaluation_titre'], 'Test Evaluation')

    @patch('xcsm.notifications.services.render_to_string')
    def test_digest_creation_and_sending(self, mock_render):
        """
        Test complet de création et d'envoi de synthèse.
        """
        mock_render.return_value = 'Rendered content'

        # Créer des notifications
        for i in range(5):
            Notification.objects.create(
                utilisateur=self.user,
                type_notification='DOCUMENT_TRAITE',
                titre=f'Notification {i}',
                message=f'Message {i}'
            )

        # Créer une synthèse
        digest = self.service.create_digest_for_user(self.user)

        self.assertIsNotNone(digest)
        self.assertEqual(digest.notifications.count(), 5)

        # Configurer le mock d'email
        self.email_mock.send_digest_email.return_value = True

        # Envoyer la synthèse
        success = self.service.send_digest_email(digest)

        self.assertTrue(success)
        self.email_mock.send_digest_email.assert_called_once_with(digest)

        # Vérifier que la synthèse est marquée comme envoyée
        digest.refresh_from_db()
        self.assertEqual(digest.statut, 'ENVOYE')