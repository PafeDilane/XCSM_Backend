"""
Vues d'authentification JWT pour XCSM.

Ce fichier contient toutes les vues liées à l'authentification et au profil utilisateur,
y compris la connexion, l'inscription, la gestion des tokens JWT, la consultation du profil,
le changement de mot de passe, ainsi que la suppression et désactivation de compte.
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, logout
from django.utils import timezone
from django.conf import settings

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    EnseignantProfileSerializer,
    EtudiantProfileSerializer,
    AdministrateurProfileSerializer
)
from .models import Utilisateur, Enseignant, Etudiant, Administrateur

# =============================================================================
# SECTION 0 : AUTHENTIFICATION ET GESTION DES TOKENS JWT
# =============================================================================

class LoginView(generics.GenericAPIView):
    """
    Vue de connexion personnalisée avec JWT.

    URL: POST /api/v1/auth/login/
    Permissions: Autorisé à tous
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """
    Vue d'inscription pour les nouveaux utilisateurs.

    URL: POST /api/v1/auth/register/
    Permissions: Autorisé à tous
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Utilisateur.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        # Génération des tokens JWT
        refresh = RefreshToken.for_user(user)

        # Construction de la réponse avec informations utilisateur
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'type_compte': user.type_compte,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'photo_url': user.photo_url.url if user.photo_url else None,
            }
        }

        # Ajout des informations de profil spécifiques
        try:
            if user.type_compte == 'ENSEIGNANT':
                data['user']['enseignant'] = {
                    'specialite': user.profil_enseignant.specialite,
                    'departement': user.profil_enseignant.departement
                }
            elif user.type_compte == 'ETUDIANT':
                data['user']['etudiant'] = {
                    'matricule': user.profil_etudiant.matricule,
                    'niveau': user.profil_etudiant.niveau,
                    'filiere': user.profil_etudiant.filiere
                }
            elif user.type_compte == 'ADMIN':
                data['user']['admin'] = {
                    'role_admin': user.profil_admin.role_admin,
                    'permissions': user.profil_admin.permissions
                }
        except:
            pass

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()


class RefreshTokenView(TokenRefreshView):
    """
    Vue pour rafraîchir un token JWT expiré.

    URL: POST /api/v1/auth/refresh/
    Permissions: Autorisé à tous
    """
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    Vue de déconnexion. Permet de blacklister le refresh token.

    URL: POST /api/v1/auth/logout/
    Permissions: Utilisateur authentifié
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token requis"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Token invalide", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# SECTION 1 : PROFIL UTILISATEUR
# =============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter et mettre à jour le profil utilisateur.

    URL: GET/PUT /api/v1/auth/profile/
    Permissions: Utilisateur authentifié
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        response_data = serializer.data

        # Ajout des données de profil spécifiques
        try:
            if user.type_compte == 'ENSEIGNANT':
                profile_serializer = EnseignantProfileSerializer(user.profil_enseignant)
                response_data['enseignant_profile'] = profile_serializer.data
            elif user.type_compte == 'ETUDIANT':
                profile_serializer = EtudiantProfileSerializer(user.profil_etudiant)
                response_data['etudiant_profile'] = profile_serializer.data
            elif user.type_compte == 'ADMIN':
                profile_serializer = AdministrateurProfileSerializer(user.profil_admin)
                response_data['admin_profile'] = profile_serializer.data
        except:
            pass

        return Response(response_data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Mise à jour du profil spécifique si fourni
        try:
            if user.type_compte == 'ENSEIGNANT' and 'enseignant_profile' in request.data:
                profile_serializer = EnseignantProfileSerializer(
                    user.profil_enseignant,
                    data=request.data['enseignant_profile'],
                    partial=partial
                )
                if profile_serializer.is_valid():
                    profile_serializer.save()
            elif user.type_compte == 'ETUDIANT' and 'etudiant_profile' in request.data:
                profile_serializer = EtudiantProfileSerializer(
                    user.profil_etudiant,
                    data=request.data['etudiant_profile'],
                    partial=partial
                )
                if profile_serializer.is_valid():
                    profile_serializer.save()
            elif user.type_compte == 'ADMIN' and 'admin_profile' in request.data:
                profile_serializer = AdministrateurProfileSerializer(
                    user.profil_admin,
                    data=request.data['admin_profile'],
                    partial=partial
                )
                if profile_serializer.is_valid():
                    profile_serializer.save()
        except:
            pass

        return Response(serializer.data)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Vue pour changer le mot de passe utilisateur.

    URL: PUT /api/v1/auth/change-password/
    Permissions: Utilisateur authentifié
    """
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not user.check_password(old_password):
            return Response({"error": "Ancien mot de passe incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Les nouveaux mots de passe ne correspondent pas"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"error": "Le mot de passe doit contenir au moins 8 caractères"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Mot de passe changé avec succès"}, status=status.HTTP_200_OK)


class VerifyTokenView(APIView):
    """
    Vue pour vérifier la validité d'un token JWT.

    URL: GET /api/v1/auth/verify/
    Permissions: Utilisateur authentifié
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "valid": True,
            "user": {
                "id": str(request.user.id),
                "username": request.user.username,
                "type_compte": request.user.type_compte
            }
        })


# =============================================================================
# SECTION 2 : SUPPRESSION ET DÉSACTIVATION DE COMPTE
# =============================================================================

class DeleteAccountView(generics.DestroyAPIView):
    """
    Vue pour supprimer définitivement le compte utilisateur.

    URL: DELETE /api/v1/auth/delete-account/
    Permissions: Utilisateur authentifié
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password')
        confirmation = request.data.get('confirmation')

        if not password:
            return Response({"error": "Le mot de passe actuel est requis pour confirmer la suppression."},
                            status=status.HTTP_400_BAD_REQUEST)

        if confirmation != "JE_SUPPRIME_MON_COMPTE":
            return Response({"error": "Vous devez écrire 'JE_SUPPRIME_MON_COMPTE' pour confirmer la suppression."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            self._log_account_deletion(user)
            self._archive_user_data(user)
            self._anonymize_user_data(user)
            self._invalidate_jwt_tokens(user)
            user.delete()
            logout(request)

            return Response({
                "message": "Votre compte a été supprimé avec succès.",
                "deletion_date": timezone.now().isoformat(),
                "note": "Toutes vos données personnelles ont été supprimées conformément au RGPD."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Une erreur est survenue lors de la suppression : {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Méthodes privées pour journalisation, archivage, anonymisation et invalidation des tokens
    def _log_account_deletion(self, user):
        import logging
        logger = logging.getLogger('xcsm.auth')
        logger.warning(f"Compte supprimé - Utilisateur: {user.username}, ID: {user.id}, Email: {user.email}, "
                       f"Rôle: {user.type_compte}, Date: {timezone.now()}")

    def _archive_user_data(self, user):
        from .models import FichierSource, Cours
        import json
        import os

        archive_dir = os.path.join(settings.MEDIA_ROOT, 'archives', 'deleted_accounts')
        os.makedirs(archive_dir, exist_ok=True)

        archive_file = os.path.join(
            archive_dir,
            f"user_{user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        archive_data = {
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "type_compte": user.type_compte,
            "date_creation": user.date_creation.isoformat() if hasattr(user, 'date_creation') else None,
            "deletion_date": timezone.now().isoformat(),
            "statistics": {
                "documents_count": FichierSource.objects.filter(enseignant__utilisateur=user).count(),
                "courses_count": Cours.objects.filter(enseignant__utilisateur=user).count(),
            }
        }

        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)

    def _anonymize_user_data(self, user):
        try:
            user.username = f"deleted_user_{user.id}"
            user.email = f"deleted_{user.id}@deleted.xcsm"
            user.first_name = "Utilisateur"
            user.last_name = "Supprimé"
            user.telephone = None if hasattr(user, 'telephone') else None
            user.photo_url = None if hasattr(user, 'photo_url') else None
            user.save()

            from .models import Notification
            Notification.objects.filter(utilisateur=user).update(
                utilisateur=None,
                envoyee_email=False,
                envoyee_push=False
            )

        except Exception as e:
            import logging
            logger = logging.getLogger('xcsm.auth')
            logger.error(f"Erreur lors de l'anonymisation: {str(e)}")

    def _invalidate_jwt_tokens(self, user):
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except ImportError:
            pass
        except Exception as e:
            import logging
            logger = logging.getLogger('xcsm.auth')
            logger.error(f"Erreur lors de l'invalidation des tokens: {str(e)}")


class DeactivateAccountView(generics.UpdateAPIView):
    """
    Vue pour désactiver temporairement un compte utilisateur.

    URL: PUT /api/v1/auth/deactivate-account/
    Permissions: Utilisateur authentifié
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password')
        reason = request.data.get('reason', 'Aucune raison fournie')

        if not password:
            return Response({"error": "Le mot de passe est requis pour confirmer la désactivation."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Désactivation du compte
            user.is_active = False
            user.save()

            import logging
            logger = logging.getLogger('xcsm.auth')
            logger.info(f"Compte désactivé - User: {user.username}, Reason: {reason}, Date: {timezone.now()}")

            # Déconnexion
            logout(request)

            return Response({
                "message": "Votre compte a été désactivé avec succès.",
                "deactivation_date": timezone.now().isoformat(),
                "reactivation_info": "Contactez l'administrateur pour réactiver votre compte.",
                "note": "Vos données sont conservées mais vous ne pouvez plus vous connecter."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Erreur lors de la désactivation : {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
