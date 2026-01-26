"""
Tests unitaires pour les modèles de notifications.
"""
import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from xcsm.notifications.models import (
    Notification,
    NotificationPreference,
    PushSubscription,
    NotificationTemplate,
    NotificationDigest
)
from xcsm.models import Utilisateur, FichierSource, Cours, Granule


class NotificationModelTest(TestCase):
    """
    Tests pour le modèle Notification.
    """

    def setUp(self):
        """
        Configuration des tests.
        """
        # Créer un utilisateur de test
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@xcsm.local',
            password='testpass123',
            type_compte='ENSEIGNANT'
        )

        # Créer un fichier source de test
        self.fichier_source = FichierSource.objects.create(
            titre='Test Document',
            enseignant=self.user.profil_enseignant,
            fichier_original='test.pdf',
            statut_traitement='TRAITE'
        )

    def test_notification_creation(self):
        """
        Test de création d'une notification.
        """
        notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Document traité',
            message='Votre document a été traité avec succès.',
            metadata={'document_id': str(self.fichier_source.id)},
            fichier_source=self.fichier_source,
            envoyee_email=True,
            envoyee_push=False,
            envoyee_in_app=True
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.utilisateur, self.user)
        self.assertEqual(notification.type_notification, 'DOCUMENT_TRAITE')
        self.assertEqual(notification.est_vue, 'NON_VUE')
        self.assertTrue(notification.envoyee_in_app)
        self.assertIsNotNone(notification.date_creation)

    def test_mark_as_read(self):
        """
        Test pour marquer une notification comme lue.
        """
        notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test',
            message='Test message'
        )

        # Vérifier l'état initial
        self.assertEqual(notification.est_vue, 'NON_VUE')
        self.assertIsNone(notification.date_lecture)

        # Marquer comme lue
        notification.marquer_comme_vue()

        # Rafraîchir depuis la base de données
        notification.refresh_from_db()

        self.assertEqual(notification.est_vue, 'VUE')
        self.assertIsNotNone(notification.date_lecture)

    def test_archive_notification(self):
        """
        Test pour archiver une notification.
        """
        notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test',
            message='Test message'
        )

        # Archiver la notification
        notification.archiver()

        # Rafraîchir depuis la base de données
        notification.refresh_from_db()

        self.assertEqual(notification.est_vue, 'ARCHIVEE')
        self.assertIsNotNone(notification.date_archivage)

    def test_get_metadata_value(self):
        """
        Test pour récupérer une valeur des métadonnées.
        """
        metadata = {
            'document_id': '12345',
            'processing_time': '2.5s',
            'granules_count': 150
        }

        notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test',
            message='Test message',
            metadata=metadata
        )

        # Récupérer des valeurs existantes
        self.assertEqual(notification.get_metadata_value('document_id'), '12345')
        self.assertEqual(notification.get_metadata_value('processing_time'), '2.5s')

        # Valeur par défaut pour une clé inexistante
        self.assertEqual(notification.get_metadata_value('non_existent', 'default'), 'default')
        self.assertIsNone(notification.get_metadata_value('non_existent'))


class NotificationPreferenceModelTest(TestCase):
    """
    Tests pour le modèle NotificationPreference.
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

    def test_preference_creation(self):
        """
        Test de création des préférences.
        """
        preference = NotificationPreference.objects.create(
            utilisateur=self.user
        )

        self.assertIsNotNone(preference.id)
        self.assertEqual(preference.utilisateur, self.user)

        # Vérifier les valeurs par défaut
        self.assertTrue(preference.document_traite_email)
        self.assertFalse(preference.document_traite_push)
        self.assertTrue(preference.document_traite_in_app)

        self.assertTrue(preference.email_notifications_enabled)
        self.assertTrue(preference.push_notifications_enabled)
        self.assertTrue(preference.in_app_notifications_enabled)

        self.assertEqual(preference.digest_frequency, 24)

    def test_get_preference_for_type(self):
        """
        Test pour récupérer une préférence spécifique.
        """
        preference = NotificationPreference.objects.create(
            utilisateur=self.user,
            document_traite_email=True,
            document_traite_push=False,
            document_traite_in_app=True,

            document_erreur_email=True,
            document_erreur_push=True,
            document_erreur_in_app=True,

            email_notifications_enabled=True,
            push_notifications_enabled=True,
            in_app_notifications_enabled=True
        )

        # Tester les préférences existantes
        self.assertTrue(preference.get_preference_for_type('DOCUMENT_TRAITE', 'email'))
        self.assertFalse(preference.get_preference_for_type('DOCUMENT_TRAITE', 'push'))
        self.assertTrue(preference.get_preference_for_type('DOCUMENT_TRAITE', 'in_app'))

        self.assertTrue(preference.get_preference_for_type('DOCUMENT_ERREUR', 'push'))

        # Type de notification non géré
        self.assertFalse(preference.get_preference_for_type('UNKNOWN_TYPE', 'email'))

    def test_preference_with_disabled_channel(self):
        """
        Test avec un canal désactivé globalement.
        """
        preference, created = NotificationPreference.objects.get_or_create(utilisateur=self.user)
        preference.document_traite_email = True
        preference.email_notifications_enabled = False
        preference.save()

        # Même si la préférence spécifique est True, le canal global est désactivé
        self.assertFalse(preference.get_preference_for_type('DOCUMENT_TRAITE', 'email'))


class PushSubscriptionModelTest(TestCase):
    """
    Tests pour le modèle PushSubscription.
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

    def test_subscription_creation(self):
        """
        Test de création d'un abonnement push.
        """
        subscription_data = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/abc123',
            'keys': {
                'p256dh': 'BNcRd...',
                'auth': '8fd7a...'
            }
        }

        subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='test-device-123',
            subscription_data=subscription_data,
            device_name='Test Browser',
            device_model='Chrome 120'
        )

        self.assertIsNotNone(subscription.id)
        self.assertEqual(subscription.utilisateur, self.user)
        self.assertEqual(subscription.device_type, 'WEB')
        self.assertEqual(subscription.device_id, 'test-device-123')
        self.assertEqual(subscription.subscription_data, subscription_data)
        self.assertTrue(subscription.is_active)
        self.assertIsNotNone(subscription.date_creation)

    def test_deactivate_subscription(self):
        """
        Test pour désactiver un abonnement.
        """
        subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='test-device-123',
            subscription_data={}
        )

        # Vérifier l'état initial
        self.assertTrue(subscription.is_active)
        self.assertIsNone(subscription.date_desactivation)

        # Désactiver
        subscription.desactiver()

        # Rafraîchir depuis la base de données
        subscription.refresh_from_db()

        self.assertFalse(subscription.is_active)
        self.assertIsNotNone(subscription.date_desactivation)


class NotificationTemplateModelTest(TestCase):
    """
    Tests pour le modèle NotificationTemplate.
    """

    def test_template_creation(self):
        """
        Test de création d'un template.
        """
        template = NotificationTemplate.objects.create(
            code='DOCUMENT_TRAITE_SUCCESS',
            nom='Document traité avec succès',
            type_notification='DOCUMENT_TRAITE',

            template_email_sujet='Votre document a été traité',
            template_email_html='<p>Bonjour {{user_name}},</p><p>Votre document {{document_title}} a été traité.</p>',
            template_email_text='Bonjour {{user_name}}, Votre document {{document_title}} a été traité.',

            template_push_titre='Document traité',
            template_push_message='{{document_title}} a été traité avec succès.',

            template_in_app_titre='Document traité',
            template_in_app_message='{{document_title}} a été traité avec succès.',

            variables_disponibles=['user_name', 'document_title', 'processing_time']
        )

        self.assertIsNotNone(template.id)
        self.assertEqual(template.code, 'DOCUMENT_TRAITE_SUCCESS')
        self.assertEqual(template.type_notification, 'DOCUMENT_TRAITE')
        self.assertTrue(template.is_active)

    def test_template_rendering(self):
        """
        Test du rendu d'un template.
        """
        template = NotificationTemplate.objects.create(
            code='TEST_TEMPLATE',
            nom='Template de test',
            type_notification='DOCUMENT_TRAITE',

            template_email_sujet='Test: {{name}}',
            template_email_html='<p>Hello {{name}}!</p>',
            template_email_text='Hello {{name}}!',

            template_push_titre='Push: {{name}}',
            template_push_message='Hello {{name}} from push!',

            template_in_app_titre='In-App: {{name}}',
            template_in_app_message='Hello {{name}} in app!'
        )

        context = {'name': 'John Doe'}

        # Tester le rendu email
        sujet, html, texte = template.render_email(context)
        self.assertEqual(sujet, 'Test: John Doe')
        self.assertEqual(html, '<p>Hello John Doe!</p>')
        self.assertEqual(texte, 'Hello John Doe!')

        # Tester le rendu push
        titre_push, message_push = template.render_push(context)
        self.assertEqual(titre_push, 'Push: John Doe')
        self.assertEqual(message_push, 'Hello John Doe from push!')

        # Tester le rendu in-app
        titre_in_app, message_in_app = template.render_in_app(context)
        self.assertEqual(titre_in_app, 'In-App: John Doe')
        self.assertEqual(message_in_app, 'Hello John Doe in app!')


class NotificationDigestModelTest(TestCase):
    """
    Tests pour le modèle NotificationDigest.
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

        # Créer des notifications de test
        self.notification1 = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Document 1 traité',
            message='Message 1'
        )

        self.notification2 = Notification.objects.create(
            utilisateur=self.user,
            type_notification='NOUVELLE_EVALUATION',
            titre='Nouvelle évaluation',
            message='Message 2'
        )

    def test_digest_creation(self):
        """
        Test de création d'une synthèse.
        """
        digest = NotificationDigest.objects.create(
            utilisateur=self.user,
            contenu_html='<p>Synthèse HTML</p>',
            contenu_text='Synthèse texte'
        )

        # Ajouter des notifications
        digest.notifications.add(self.notification1, self.notification2)

        self.assertIsNotNone(digest.id)
        self.assertEqual(digest.utilisateur, self.user)
        self.assertEqual(digest.statut, 'EN_ATTENTE')
        self.assertEqual(digest.notifications.count(), 2)
        self.assertFalse(digest.email_ouvert)
        self.assertFalse(digest.email_clique)

    def test_mark_as_sent(self):
        """
        Test pour marquer une synthèse comme envoyée.
        """
        digest = NotificationDigest.objects.create(
            utilisateur=self.user,
            contenu_html='<p>Test</p>',
            contenu_text='Test'
        )

        # Marquer comme envoyée
        digest.marquer_comme_envoye('email-12345')

        # Rafraîchir depuis la base de données
        digest.refresh_from_db()

        self.assertEqual(digest.statut, 'ENVOYE')
        self.assertIsNotNone(digest.date_envoi)
        self.assertEqual(digest.email_message_id, 'email-12345')

    def test_mark_as_opened(self):
        """
        Test pour marquer une synthèse comme ouverte.
        """
        digest = NotificationDigest.objects.create(
            utilisateur=self.user,
            contenu_html='<p>Test</p>',
            contenu_text='Test'
        )

        # Marquer comme ouverte
        digest.marquer_comme_ouvert()

        # Rafraîchir depuis la base de données
        digest.refresh_from_db()

        self.assertTrue(digest.email_ouvert)
        self.assertIsNotNone(digest.date_ouverture)

    def test_mark_as_clicked(self):
        """
        Test pour marquer une synthèse comme cliquée.
        """
        digest = NotificationDigest.objects.create(
            utilisateur=self.user,
            contenu_html='<p>Test</p>',
            contenu_text='Test'
        )

        # Marquer comme cliquée
        digest.marquer_comme_clique()

        # Rafraîchir depuis la base de données
        digest.refresh_from_db()

        self.assertTrue(digest.email_clique)
        self.assertIsNotNone(digest.date_clic)


class ModelIntegrationTest(TestCase):
    """
    Tests d'intégration entre les modèles.
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

    def test_user_notification_relationship(self):
        """
        Test des relations utilisateur-notification.
        """
        # Créer des notifications
        for i in range(5):
            Notification.objects.create(
                utilisateur=self.user,
                type_notification='DOCUMENT_TRAITE',
                titre=f'Notification {i}',
                message=f'Message {i}'
            )

        # Vérifier les relations
        self.assertEqual(self.user.notifications.count(), 5)

        # Vérifier les préférences
        preference = NotificationPreference.objects.get(utilisateur=self.user)
        self.assertEqual(preference.utilisateur, self.user)

    def test_notification_digest_relationship(self):
        """
        Test des relations notification-synthèse.
        """
        # Créer des notifications
        notifications = []
        for i in range(3):
            notification = Notification.objects.create(
                utilisateur=self.user,
                type_notification='DOCUMENT_TRAITE',
                titre=f'Notification {i}',
                message=f'Message {i}'
            )
            notifications.append(notification)

        # Créer une synthèse
        digest = NotificationDigest.objects.create(
            utilisateur=self.user,
            contenu_html='<p>Synthèse</p>',
            contenu_text='Synthèse'
        )

        # Associer les notifications
        digest.notifications.set(notifications)

        # Vérifier les relations
        self.assertEqual(digest.notifications.count(), 3)

        for notification in notifications:
            self.assertEqual(notification.digests.count(), 1)
            self.assertEqual(notification.digests.first(), digest)

    def test_cascade_delete(self):
        """
        Test de suppression en cascade.
        """
        # Créer des notifications, préférences et abonnements
        notification = Notification.objects.create(
            utilisateur=self.user,
            type_notification='DOCUMENT_TRAITE',
            titre='Test',
            message='Test'
        )

        preference = NotificationPreference.objects.get(utilisateur=self.user)

        subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='test-device',
            subscription_data={}
        )

        # Supprimer l'utilisateur
        self.user.delete()

        # Vérifier que les objets liés sont supprimés
        self.assertEqual(Notification.objects.filter(id=notification.id).count(), 0)
        self.assertEqual(NotificationPreference.objects.filter(id=preference.id).count(), 0)
        self.assertEqual(PushSubscription.objects.filter(id=subscription.id).count(), 0)