"""
Tests unitaires pour les vues de notifications.
"""
import json
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone

from xcsm.models import Utilisateur
from xcsm.notifications.models import (
    Notification,
    NotificationPreference,
    PushSubscription,
    NotificationTemplate,
    NotificationDigest
)


class NotificationViewSetTest(APITestCase):
    """
    Tests pour le ViewSet des notifications.
    """

    def setUp(self):
        """
        Configuration des tests.
        """
        # Créer des utilisateurs avec différents rôles
        self.admin_user = Utilisateur.objects.create_user(
            username='admin',
            email='admin@xcsm.local',
            password='adminpass123',
            type_compte='ADMIN',
            is_staff=True
        )

        self.teacher_user = Utilisateur.objects.create_user(
            username='teacher',
            email='teacher@xcsm.local',
            password='teacherpass123',
            type_compte='ENSEIGNANT'
        )

        self.student_user = Utilisateur.objects.create_user(
            username='student',
            email='student@xcsm.local',
            password='studentpass123',
            type_compte='ETUDIANT'
        )

        # Créer les préférences de notification
        NotificationPreference.objects.get_or_create(utilisateur=self.teacher_user)
        NotificationPreference.objects.get_or_create(utilisateur=self.student_user)

        # Créer des notifications de test
        self.notification1 = Notification.objects.create(
            utilisateur=self.teacher_user,
            type_notification='DOCUMENT_TRAITE',
            titre='Document traité',
            message='Votre document a été traité'
        )

        self.notification2 = Notification.objects.create(
            utilisateur=self.student_user,
            type_notification='NOUVELLE_EVALUATION',
            titre='Nouvelle évaluation',
            message='Une nouvelle évaluation est disponible'
        )

        self.notification3 = Notification.objects.create(
            utilisateur=self.teacher_user,
            type_notification='SYSTEM_MAINTENANCE',
            titre='Maintenance système',
            message='Maintenance planifiée',
            est_vue='VUE'
        )

        # Initialiser le client API
        self.client = APIClient()

    def authenticate_user(self, user):
        """
        Authentifier un utilisateur pour les tests.
        """
        self.client.force_authenticate(user=user)

    # Tests d'authentification
    def test_list_notifications_unauthenticated(self):
        """
        Test d'accès non authentifié à la liste des notifications.
        """
        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notifications_teacher(self):
        """
        Test d'accès d'un enseignant à ses notifications.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que l'enseignant ne voit que ses propres notifications
        notifications = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(notifications), 2)  # 2 notifications pour l'enseignant

        for notification in notifications:
            self.assertEqual(notification['utilisateur'], self.teacher_user.id)

    def test_list_notifications_admin(self):
        """
        Test d'accès d'un admin à toutes les notifications.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que l'admin voit toutes les notifications
        notifications = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(notifications), 3)  # Toutes les notifications

    # Tests de filtrage
    def test_filter_notifications_by_type(self):
        """
        Test de filtrage par type de notification.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-list')
        response = self.client.get(url, {'type_notification': 'DOCUMENT_TRAITE'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]['type_notification'], 'DOCUMENT_TRAITE')

    def test_filter_notifications_by_status(self):
        """
        Test de filtrage par statut.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-list')
        response = self.client.get(url, {'est_vue': 'NON_VUE'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(notifications), 1)  # Une seule notification non lue
        self.assertEqual(notifications[0]['est_vue'], 'NON_VUE')

    # Tests de détail
    def test_retrieve_notification_owner(self):
        """
        Test de récupération d'une notification par son propriétaire.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-detail', args=[str(self.notification1.id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.notification1.id))
        self.assertEqual(response.data['titre'], 'Document traité')

    def test_retrieve_notification_admin(self):
        """
        Test de récupération d'une notification par un admin.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('notification-detail', args=[str(self.notification2.id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.notification2.id))

    def test_retrieve_notification_unauthorized(self):
        """
        Test de récupération non autorisée d'une notification.
        """
        self.authenticate_user(self.teacher_user)

        # L'enseignant essaie d'accéder à la notification de l'étudiant
        url = reverse('notification-detail', args=[str(self.notification2.id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Tests d'actions personnalisées
    def test_mark_as_read(self):
        """
        Test de marquage de notifications comme lues.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-mark-as-read')
        data = {
            'notification_ids': [str(self.notification1.id)]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)

        # Vérifier que la notification est maintenant marquée comme lue
        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.est_vue, 'VUE')
        self.assertIsNotNone(self.notification1.date_lecture)

    def test_mark_all_read(self):
        """
        Test de marquage de toutes les notifications comme lues.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-mark-all-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)

        # Vérifier que toutes les notifications non lues sont maintenant lues
        unread_count = Notification.objects.filter(
            utilisateur=self.teacher_user,
            est_vue='NON_VUE'
        ).count()

        self.assertEqual(unread_count, 0)

    def test_unread_count(self):
        """
        Test de récupération du nombre de notifications non lues.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-unread-count')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)  # 1 notification non lue

    def test_recent_notifications(self):
        """
        Test de récupération des notifications récentes.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-recent')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = response.data
        self.assertLessEqual(len(notifications), 10)

    def test_archive_notification(self):
        """
        Test d'archivage d'une notification.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('notification-archive', args=[str(self.notification1.id)])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que la notification est archivée
        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.est_vue, 'ARCHIVEE')
        self.assertIsNotNone(self.notification1.date_archivage)


class NotificationPreferenceViewSetTest(APITestCase):
    """
    Tests pour le ViewSet des préférences de notifications.
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

        self.admin_user = Utilisateur.objects.create_user(
            username='admin',
            email='admin@xcsm.local',
            password='adminpass123',
            type_compte='ADMIN',
            is_staff=True
        )

        # Récupérer et configurer les préférences (créées par signal)
        self.preference = NotificationPreference.objects.get(utilisateur=self.user)
        self.preference.document_traite_email = True
        self.preference.document_traite_push = False
        self.preference.digest_frequency = 24
        self.preference.save()

        self.client = APIClient()

    def authenticate_user(self, user):
        """
        Authentifier un utilisateur pour les tests.
        """
        self.client.force_authenticate(user=user)

    def test_retrieve_preferences(self):
        """
        Test de récupération des préférences.
        """
        self.authenticate_user(self.user)

        url = reverse('notificationpreference-detail', args=[str(self.preference.id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.preference.id))
        self.assertTrue(response.data['document_traite_email'])
        self.assertFalse(response.data['document_traite_push'])
        self.assertEqual(response.data['digest_frequency'], 24)

    def test_retrieve_preferences_auto(self):
        """
        Test de récupération automatique des préférences de l'utilisateur.
        """
        self.authenticate_user(self.user)

        # Ne pas spécifier l'ID - doit retourner les préférences de l'utilisateur
        url = reverse('notificationpreference-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        preferences = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(preferences), 1)
        self.assertEqual(preferences[0]['utilisateur'], self.user.id)

    def test_update_preferences(self):
        """
        Test de mise à jour des préférences.
        """
        self.authenticate_user(self.user)

        url = reverse('notificationpreference-detail', args=[str(self.preference.id)])
        data = {
            'document_traite_email': False,
            'document_traite_push': True,
            'digest_frequency': 12
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les modifications
        self.preference.refresh_from_db()
        self.assertFalse(self.preference.document_traite_email)
        self.assertTrue(self.preference.document_traite_push)
        self.assertEqual(self.preference.digest_frequency, 12)

    def test_partial_update_preferences(self):
        """
        Test de mise à jour partielle des préférences.
        """
        self.authenticate_user(self.user)

        url = reverse('notificationpreference-detail', args=[str(self.preference.id)])
        data = {
            'digest_frequency': 168  # Hebdomadaire
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que seul le champ spécifié a été modifié
        self.preference.refresh_from_db()
        self.assertEqual(self.preference.digest_frequency, 168)
        self.assertTrue(self.preference.document_traite_email)  # Inchangé

    def test_my_preferences_endpoint(self):
        """
        Test du endpoint 'mine' pour les préférences.
        """
        self.authenticate_user(self.user)

        url = reverse('notificationpreference-mine')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['utilisateur'], self.user.id)

    def test_create_preferences_duplicate(self):
        """
        Test de création de préférences en double.
        """
        self.authenticate_user(self.user)

        url = reverse('notificationpreference-list')
        data = {
            'utilisateur': self.user.id,
            'document_traite_email': True
        }

        response = self.client.post(url, data, format='json')

        # Doit échouer car des préférences existent déjà
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PushSubscriptionViewSetTest(APITestCase):
    """
    Tests pour le ViewSet des abonnements push.
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

        # Créer un abonnement
        self.subscription = PushSubscription.objects.create(
            utilisateur=self.user,
            device_type='WEB',
            device_id='test-device-123',
            subscription_data={
                'endpoint': 'https://example.com',
                'keys': {'p256dh': 'test', 'auth': 'test'}
            }
        )

        self.client = APIClient()
        self.authenticate_user(self.user)

    def authenticate_user(self, user):
        """
        Authentifier un utilisateur pour les tests.
        """
        self.client.force_authenticate(user=user)

    def test_list_subscriptions(self):
        """
        Test de liste des abonnements.
        """
        url = reverse('pushsubscription-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        subscriptions = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(subscriptions), 1)
        self.assertEqual(subscriptions[0]['device_id'], 'test-device-123')

    def test_create_subscription(self):
        """
        Test de création d'un abonnement.
        """
        url = reverse('pushsubscription-list')
        data = {
            'device_type': 'ANDROID',
            'device_id': 'new-device-456',
            'subscription_data': {'token': 'firebase-token-123'},
            'device_name': 'Test Phone',
            'device_model': 'Pixel 6'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['device_id'], 'new-device-456')
        self.assertEqual(response.data['device_type'], 'ANDROID')

        # Vérifier la création dans la base de données
        subscription = PushSubscription.objects.get(device_id='new-device-456')
        self.assertEqual(subscription.utilisateur, self.user)
        self.assertTrue(subscription.is_active)

    def test_update_existing_subscription(self):
        """
        Test de mise à jour d'un abonnement existant.
        """
        # Mettre à jour l'abonnement existant
        url = reverse('pushsubscription-detail', args=[str(self.subscription.id)])
        data = {
            'subscription_data': {
                'endpoint': 'https://updated.com',
                'keys': {'p256dh': 'updated', 'auth': 'updated'}
            },
            'device_name': 'Updated Browser'
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les modifications
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.subscription_data['endpoint'], 'https://updated.com')
        self.assertEqual(self.subscription.device_name, 'Updated Browser')

    def test_unsubscribe_device(self):
        """
        Test de désabonnement d'un appareil.
        """
        url = reverse('pushsubscription-unsubscribe')
        data = {
            'device_id': 'test-device-123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que l'abonnement est désactivé
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.is_active)
        self.assertIsNotNone(self.subscription.date_desactivation)

    def test_unsubscribe_nonexistent_device(self):
        """
        Test de désabonnement d'un appareil inexistant.
        """
        url = reverse('pushsubscription-unsubscribe')
        data = {
            'device_id': 'non-existent-device'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NotificationTemplateViewSetTest(APITestCase):
    """
    Tests pour le ViewSet des templates de notifications.
    """

    def setUp(self):
        """
        Configuration des tests.
        """
        self.admin_user = Utilisateur.objects.create_user(
            username='admin',
            email='admin@xcsm.local',
            password='adminpass123',
            type_compte='ADMIN',
            is_staff=True
        )

        self.regular_user = Utilisateur.objects.create_user(
            username='regular',
            email='regular@xcsm.local',
            password='regularpass123',
            type_compte='ENSEIGNANT'
        )

        # Créer un template
        self.template = NotificationTemplate.objects.create(
            code='TEST_TEMPLATE',
            nom='Template de test',
            type_notification='DOCUMENT_TRAITE',
            template_email_sujet='Test: {{name}}',
            template_email_html='<p>Hello {{name}}!</p>',
            template_email_text='Hello {{name}}!',
            template_push_titre='Push: {{name}}',
            template_push_message='Hello {{name}} from push!',
            template_in_app_titre='In-App: {{name}}',
            template_in_app_message='Hello {{name}} in app!',
            variables_disponibles=['name']
        )

        self.client = APIClient()

    def authenticate_user(self, user):
        """
        Authentifier un utilisateur pour les tests.
        """
        self.client.force_authenticate(user=user)

    def test_list_templates_admin(self):
        """
        Test de liste des templates par un admin.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('notificationtemplate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        templates = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['code'], 'TEST_TEMPLATE')

    def test_list_templates_non_admin(self):
        """
        Test de liste des templates par un non-admin.
        """
        self.authenticate_user(self.regular_user)

        url = reverse('notificationtemplate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_template_admin(self):
        """
        Test de création de template par un admin.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('notificationtemplate-list')
        data = {
            'code': 'NEW_TEMPLATE',
            'nom': 'Nouveau template',
            'type_notification': 'NOUVELLE_EVALUATION',
            'template_email_sujet': 'Nouvelle évaluation: {{cours}}',
            'template_email_html': '<p>Nouvelle évaluation pour {{cours}}</p>',
            'template_email_text': 'Nouvelle évaluation pour {{cours}}',
            'template_push_titre': 'Nouvelle évaluation',
            'template_push_message': 'Nouvelle évaluation pour {{cours}}',
            'template_in_app_titre': 'Nouvelle évaluation',
            'template_in_app_message': 'Nouvelle évaluation pour {{cours}}',
            'variables_disponibles': ['cours', 'enseignant'],
            'is_active': True
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'NEW_TEMPLATE')

        # Vérifier la création dans la base de données
        template = NotificationTemplate.objects.get(code='NEW_TEMPLATE')
        self.assertEqual(template.nom, 'Nouveau template')
        self.assertEqual(template.type_notification, 'NOUVELLE_EVALUATION')

    def test_test_template(self):
        """
        Test du endpoint de test de template.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('notificationtemplate-test', args=[str(self.template.id)])
        data = {
            'context': {'name': 'John Doe'}
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier le rendu
        self.assertIn('email', response.data)
        self.assertIn('push', response.data)
        self.assertIn('in_app', response.data)

        self.assertEqual(response.data['email']['sujet'], 'Test: John Doe')
        self.assertIn('Hello John Doe!', response.data['email']['html_preview'])


class BulkNotificationCreateViewTest(APITestCase):
    """
    Tests pour la vue de création en masse de notifications.
    """

    def setUp(self):
        """
        Configuration des tests.
        """
        self.admin_user = Utilisateur.objects.create_user(
            username='admin',
            email='admin@xcsm.local',
            password='adminpass123',
            type_compte='ADMIN',
            is_staff=True
        )

        self.teacher_user = Utilisateur.objects.create_user(
            username='teacher',
            email='teacher@xcsm.local',
            password='teacherpass123',
            type_compte='ENSEIGNANT'
        )

        self.student1 = Utilisateur.objects.create_user(
            username='student1',
            email='student1@xcsm.local',
            password='studentpass123',
            type_compte='ETUDIANT'
        )

        self.student2 = Utilisateur.objects.create_user(
            username='student2',
            email='student2@xcsm.local',
            password='studentpass123',
            type_compte='ETUDIANT'
        )

        self.client = APIClient()

    def authenticate_user(self, user):
        """
        Authentifier un utilisateur pour les tests.
        """
        self.client.force_authenticate(user=user)

    def test_create_bulk_notifications_admin(self):
        """
        Test de création en masse par un admin.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('bulk-notification-create')
        data = {
            'utilisateur_ids': [str(self.student1.id), str(self.student2.id)],
            'type_notification': 'NOUVELLE_EVALUATION',
            'titre': 'Nouvelle évaluation disponible',
            'message': 'Une nouvelle évaluation a été publiée pour votre cours.',
            'metadata': {'cours_id': '123', 'date_limite': '2024-12-31'},
            'envoyer_email': False,
            'envoyer_push': False,
            'envoyer_in_app': True
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 2)

        # Vérifier la création des notifications
        notifications = Notification.objects.filter(
            type_notification='NOUVELLE_EVALUATION',
            titre='Nouvelle évaluation disponible'
        )

        self.assertEqual(notifications.count(), 2)

        # Vérifier que chaque étudiant a reçu une notification
        student1_notifications = notifications.filter(utilisateur=self.student1)
        student2_notifications = notifications.filter(utilisateur=self.student2)

        self.assertEqual(student1_notifications.count(), 1)
        self.assertEqual(student2_notifications.count(), 1)

    def test_create_bulk_notifications_teacher(self):
        """
        Test de création en masse par un enseignant.
        """
        self.authenticate_user(self.teacher_user)

        url = reverse('bulk-notification-create')
        data = {
            'utilisateur_ids': [str(self.student1.id)],
            'type_notification': 'NOUVELLE_EVALUATION',
            'titre': 'Test',
            'message': 'Test message'
        }

        response = self.client.post(url, data, format='json')

        # Les enseignants peuvent aussi créer des notifications en masse
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_bulk_notifications_student(self):
        """
        Test de création en masse par un étudiant (non autorisé).
        """
        self.authenticate_user(self.student1)

        url = reverse('bulk-notification-create')
        data = {
            'utilisateur_ids': [str(self.student2.id)],
            'type_notification': 'NOUVELLE_EVALUATION',
            'titre': 'Test',
            'message': 'Test message'
        }

        response = self.client.post(url, data, format='json')

        # Les étudiants ne peuvent pas créer de notifications en masse
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_bulk_notifications_invalid_users(self):
        """
        Test avec des IDs d'utilisateurs invalides.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('bulk-notification-create')
        data = {
            'utilisateur_ids': [str(self.student1.id), '00000000-0000-0000-0000-000000000000'],
            'type_notification': 'NOUVELLE_EVALUATION',
            'titre': 'Test',
            'message': 'Test message'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non trouvés', str(response.data))


class NotificationStatsViewTest(APITestCase):
    """
    Tests pour la vue des statistiques de notifications.
    """

    def setUp(self):
        """
        Configuration des tests.
        """
        self.admin_user = Utilisateur.objects.create_user(
            username='admin',
            email='admin@xcsm.local',
            password='adminpass123',
            type_compte='ADMIN',
            is_staff=True
        )

        self.regular_user = Utilisateur.objects.create_user(
            username='regular',
            email='regular@xcsm.local',
            password='regularpass123',
            type_compte='ENSEIGNANT'
        )

        # Créer des notifications pour les tests
        for i in range(5):
            Notification.objects.create(
                utilisateur=self.regular_user,
                type_notification='DOCUMENT_TRAITE',
                titre=f'Notification {i}',
                message=f'Message {i}',
                est_vue='VUE' if i < 3 else 'NON_VUE',
                envoyee_email=True,
                envoyee_push=(i % 2 == 0)
            )

        self.client = APIClient()

    def authenticate_user(self, user):
        """
        Authentifier un utilisateur pour les tests.
        """
        self.client.force_authenticate(user=user)

    def test_admin_stats(self):
        """
        Test des statistiques pour un admin.
        """
        self.authenticate_user(self.admin_user)

        url = reverse('notification-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les statistiques globales
        self.assertIn('global', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('by_channel', response.data)

        global_stats = response.data['global']
        self.assertEqual(global_stats['total'], 5)
        self.assertEqual(global_stats['unread'], 2)
        self.assertEqual(global_stats['read'], 3)

        # Vérifier les statistiques par canal
        channel_stats = response.data['by_channel']
        self.assertEqual(channel_stats['email'], 5)  # Tous les emails envoyés
        self.assertEqual(channel_stats['push'], 3)   # 3 notifications push (i pair)

    def test_regular_user_stats(self):
        """
        Test des statistiques pour un utilisateur régulier.
        """
        self.authenticate_user(self.regular_user)

        url = reverse('notification-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier les statistiques personnelles
        self.assertIn('personal', response.data)

        personal_stats = response.data['personal']
        self.assertEqual(personal_stats['total'], 5)
        self.assertEqual(personal_stats['unread'], 2)
        self.assertEqual(personal_stats['read'], 3)

        # Vérifier les statistiques récentes
        self.assertIn('recent_7_days', personal_stats)