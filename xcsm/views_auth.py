"""
Vues d'authentification JWT pour XCSM
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    EnseignantProfileSerializer,
    EtudiantProfileSerializer,
    AdministrateurProfileSerializer
)
from .models import Utilisateur, Enseignant, Etudiant, Administrateur


class LoginView(generics.GenericAPIView):
    """
    Vue de connexion personnalisée avec serializer JWT
    URL: POST /api/v1/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {"error": "Identifiants invalides", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """
    Vue d'inscription pour les nouveaux utilisateurs
    URL: POST /api/v1/auth/register/
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Utilisateur.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        # Génération des tokens
        refresh = RefreshToken.for_user(user)

        # Construction de la réponse
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

        # Ajout des informations de profil
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
    Vue pour rafraîchir un token JWT
    URL: POST /api/v1/auth/refresh/
    """
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    Vue de déconnexion (blacklist du refresh token)
    URL: POST /api/v1/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Déconnexion réussie"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Token invalide", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter/mettre à jour le profil utilisateur
    URL: GET/PUT /api/v1/auth/profile/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)

        response_data = serializer.data

        # Ajout des informations de profil spécifiques
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

        return Response(serializer.data)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Vue pour changer le mot de passe
    URL: PUT /api/v1/auth/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not user.check_password(old_password):
            return Response(
                {"error": "Ancien mot de passe incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "Les nouveaux mots de passe ne correspondent pas"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {"error": "Le mot de passe doit contenir au moins 8 caractères"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Mot de passe changé avec succès"},
            status=status.HTTP_200_OK
        )


class VerifyTokenView(APIView):
    """
    Vue pour vérifier la validité d'un token
    URL: POST /api/v1/auth/verify/
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