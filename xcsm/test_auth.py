"""
Tests unitaires pour le système d'authentification et de gestion des utilisateurs.
Ce fichier valide la sécurité des accès, la validité des tokens JWT et 
le respect des processus métiers (Profils, Blacklist, Désactivation).
"""
import uuid
import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from xcsm.models import Utilisateur, Enseignant


class AuthenticationTests(APITestCase):
    """
    Suite de tests pour l'authentification et les profils.
    """

    def setUp(self):
        """
        Initialisation de l'environnement de test :
        - Création d'un utilisateur de base.
        - Création d'un profil Enseignant associé.
        - Préparation des URLs.
        """
        self.password = 'TestPassword123'
        self.user = Utilisateur.objects.create_user(
            username='authuser',
            email='auth@xcsm.local',
            password=self.password,
            type_compte='ENSEIGNANT'
        )
        self.enseignant = Enseignant.objects.create(
            utilisateur=self.user,
            specialite='Informatique',
            departement='Tests'
        )
        
        # Mapping des noms d'URLs définis dans urls.py
        self.login_url = reverse('auth-login')
        self.register_url = reverse('auth-register')
        self.refresh_url = reverse('auth-refresh')
        self.logout_url = reverse('auth-logout')
        self.profile_url = reverse('auth-profile')
        self.verify_url = reverse('auth-verify')
        self.change_password_url = reverse('auth-change-password')

    def test_login_success(self):
        """
        Vérifie qu'un utilisateur valide peut se connecter et recevoir ses tokens.
        """
        data = {
            'username': 'authuser',
            'password': self.password
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # On s'assure que les tokens sont présents dans le corps de la réponse
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'authuser')

    def test_login_invalid_credentials(self):
        """
        Vérifie que la connexion échoue avec de mauvais identifiants.
        """
        data = {
            'username': 'authuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        # Normalement 401 si credentials invalides, ou 403 si configuré ainsi
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_success(self):
        """
        Vérifie qu'un nouvel utilisateur peut s'inscrire et que son profil métier
        est créé automatiquement.
        """
        data = {
            'username': 'newuser',
            'email': 'new@xcsm.local',
            'password': 'NewPassword123',
            'confirm_password': 'NewPassword123',
            'type_compte': 'ENSEIGNANT',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Vérification en base de données
        self.assertTrue(Utilisateur.objects.filter(username='newuser').exists())
        self.assertTrue(Enseignant.objects.filter(utilisateur__username='newuser').exists())

    def test_refresh_token(self):
        """
        Vérifie le fonctionnement du renouvellement de token.
        """
        refresh = RefreshToken.for_user(self.user)
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout_and_blacklist(self):
        """
        Vérifie que la déconnexion invalide définitivement le refresh token.
        """
        self.client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        data = {'refresh': str(refresh)}
        # 1. Déconnexion
        response = self.client.post(self.logout_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Tentative de réutilisation du même refresh token (doit échouer)
        response_retry = self.client.post(self.refresh_url, data)
        self.assertEqual(response_retry.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_profile(self):
        """
        Vérifie que l'utilisateur peut consulter ses données de profil complètes.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'authuser')
        self.assertIn('enseignant_profile', response.data)

    def test_update_user_profile(self):
        """
        Vérifie la mise à jour des informations de compte et métier.
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'first_name': 'UpdatedName',
            'enseignant_profile': {
                'specialite': 'Informatique Quantique',
                'departement': 'Tests'
            }
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Validation des changements persistés
        self.user.refresh_from_db()
        self.enseignant.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedName')
        self.assertEqual(self.enseignant.specialite, 'Informatique Quantique')

    def test_change_password(self):
        """
        Vérifie le changement de mot de passe sécurisé.
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': self.password,
            'new_password': 'NewSecurePassword123',
            'confirm_password': 'NewSecurePassword123'
        }
        response = self.client.put(self.change_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password('NewSecurePassword123'))

    def test_verify_token(self):
        """
        Vérifie le point de terminaison de validation de token (pour le frontend).
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])

    def test_deactivate_account(self):
        """
        Vérifie la désactivation (soft lock) du compte.
        """
        self.client.force_authenticate(user=self.user)
        deactivate_url = reverse('auth-deactivate-account')
        data = {
            'password': self.password,
            'reason': 'Test de désactivation'
        }
        response = self.client.put(deactivate_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # L'objet existe toujours mais is_active est à False
        self.assertFalse(self.user.is_active)

    def test_delete_account(self):
        """
        Vérifie la suppression définitive (conformité RGPD).
        """
        self.client.force_authenticate(user=self.user)
        delete_url = reverse('auth-delete-account')
        data = {
            'password': self.password,
            'confirmation': 'JE_SUPPRIME_MON_COMPTE'
        }
        response = self.client.delete(delete_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # L'utilisateur ne doit plus exister en base
        with self.assertRaises(Utilisateur.DoesNotExist):
            Utilisateur.objects.get(username='authuser')
