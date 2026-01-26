"""
Vues d'authentification JWT pour XCSM.

Ce fichier orchestre la logique d'accès à la plateforme : 
- Inscription avec création automatique de profils métiers.
- Connexion sécurisée via tokens JWT.
- Gestion du cycle de vie du compte (Profil, Mot de passe, Désactivation, Suppression).
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, logout
from django.utils import timezone
from django.conf import settings

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    EnseignantProfileSerializer,
    EtudiantProfileSerializer,
    AdministrateurProfileSerializer,
    AccountDeletionSerializer,
    AccountDeactivationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .models import Utilisateur, Enseignant, Etudiant, Administrateur

# =============================================================================
# SECTION 0 : AUTHENTIFICATION ET GESTION DES TOKENS JWT
# =============================================================================

class LoginView(generics.GenericAPIView):
    """
    Vue de connexion (Login).
    Utilise 'CustomTokenObtainPairSerializer' pour retourner les tokens
    ainsi que les informations de base de l'utilisateur en une seule requête.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny] # Ouvert à tous

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Retourne Access Token + Refresh Token + Infos User
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """
    Vue d'inscription (Inscription).
    Crée un compte utilisateur et déclenche automatiquement (via signaux) 
    la création du profil métier (Enseignant/Etudiant) et l'envoi de l'email de bienvenue.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Utilisateur.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        # On connecte immédiatement l'utilisateur après inscription en générant ses tokens
        refresh = RefreshToken.for_user(user)

        # Préparation du dictionnaire de réponse complet
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

        # Injection dynamique des informations de profil selon le rôle
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
        except Exception:
            # En cas de problème de lecture du profil, on renvoie les données de base
            pass

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()


class RefreshTokenView(TokenRefreshView):
    """
    Vue de rafraîchissement. Permet d'obtenir un nouvel 'access token' 
    sans redemander les identifiants, tant que le 'refresh token' est valide.
    """
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    Vue de déconnexion. 
    Invalide le refresh token en le plaçant dans la 'blacklist' côté serveur.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token requis"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist() # Rend le token inutilisable pour de futurs refreshs

            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Token invalide ou déjà expiré", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# SECTION 1 : PROFIL UTILISATEUR
# =============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue de gestion du profil personnel.
    Permet de lire (GET) ou mettre à jour (PUT/PATCH) les infos de base et métier.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # On retourne toujours l'utilisateur connecté
        return self.request.user

    def get(self, request, *args, **kwargs):
        """Récupère les infos utilisateur agrégées avec son profil spécifique."""
        user = self.get_object()
        serializer = self.get_serializer(user)
        response_data = serializer.data

        # Ajout des données de profil spécifiques selon le rôle
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
        except Exception:
            pass

        return Response(response_data)

    def update(self, request, *args, **kwargs):
        """Met à jour les informations de base et délégue la mise à jour des profils métiers."""
        partial = kwargs.pop('partial', False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Mise à jour des profils imbriqués (Logique manuelle car DRF ne gère pas nativement
        # les mises à jour imbriquées sur des relations inverses 1-1 sans config complexe)
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
        except Exception:
            pass

        return Response(serializer.data)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Vue de changement sécurisé du mot de passe.
    Nécessite la validation de l'ancien mot de passe.
    """
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        # Vérifications de sécurité
        if not user.check_password(old_password):
            return Response({"error": "Ancien mot de passe incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Les nouveaux mots de passe ne correspondent pas"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"error": "Le mot de passe doit contenir au moins 8 caractères"}, status=status.HTTP_400_BAD_REQUEST)

        # Changement effectif
        user.set_password(new_password)
        user.save()

        return Response({"message": "Mot de passe changé avec succès"}, status=status.HTTP_200_OK)


class VerifyTokenView(APIView):
    """
    Vue utilitaire pour le Frontend.
    Permet de vérifier si le token stocké localement est toujours valide et pour quel utilisateur.
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
    Vue critique de suppression de compte (Conformité RGPD).
    Efface les données personnelles, anonymise les journaux et révoque les tokens.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password')
        confirmation = request.data.get('confirmation')

        # Double validation (Mot de passe + Phrase de sécurité)
        if not password:
            return Response({"error": "Le mot de passe actuel est requis pour cette action."}, status=status.HTTP_400_BAD_REQUEST)

        if confirmation != "JE_SUPPRIME_MON_COMPTE":
            return Response({"error": "Phrase de confirmation incorrecte."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Journalisation (sans données privées)
            self._log_account_deletion(user)
            # 2. Sauvegarde des stats d'usage avant suppression
            self._archive_user_data(user)
            # 3. Nettoyage des références (anonymisation)
            self._anonymize_user_data(user)
            # 4. Blocage des accès
            self._invalidate_jwt_tokens(user)
            
            # 5. Suppression réelle de l'objet utilisateur
            user.delete()
            logout(request)

            return Response({
                "message": "Votre compte a été supprimé définitivement.",
                "note": "Vos données personnelles ont été traitées selon les règles de confidentialité."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Erreur système lors de la suppression : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _log_account_deletion(self, user):
        """Enregistre l'événement pour l'audit admin."""
        import logging
        logger = logging.getLogger('xcsm.auth')
        logger.warning(f"ACTION: Suppression de compte - ID: {user.id}, Date: {timezone.now()}")

    def _archive_user_data(self, user):
        """Génère un rapport JSON des activités avant suppression."""
        from .models import FichierSource, Cours
        import json
        import os

        # Chemin de stockage sécurisé
        archive_dir = os.path.join(settings.MEDIA_ROOT, 'archives', 'deleted_accounts')
        os.makedirs(archive_dir, exist_ok=True)

        archive_file = os.path.join(archive_dir, f"backup_{user.id}_{timezone.now().strftime('%Y%m%d')}.json")

        stats = {
            "user_id": str(user.id),
            "type_compte": user.type_compte,
            "deletion_date": timezone.now().isoformat(),
            "activity": {
                "uploads": FichierSource.objects.filter(enseignant__utilisateur=user).count(),
                "courses": Cours.objects.filter(enseignant__utilisateur=user).count(),
            }
        }

        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

    def _anonymize_user_data(self, user):
        """Détache les liens vers les notifications pour éviter les erreurs d'intégrité."""
        try:
            from .notifications.models import Notification
            # On conserve les notifications mais on retire le lien avec l'utilisateur
            Notification.objects.filter(utilisateur=user).update(utilisateur=None)
        except Exception:
            pass

    def _invalidate_jwt_tokens(self, user):
        """Révoque tous les tokens actifs pour cet utilisateur."""
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass


class DeactivateAccountView(generics.UpdateAPIView):
    """
    Vue de désactivation temporaire.
    L'utilisateur ne peut plus se connecter, mais ses données sont conservées intactes.
    Une intervention admin est nécessaire pour la réactivation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password')
        reason = request.data.get('reason', 'Non précisé')

        if not user.check_password(password):
            return Response({"error": "Mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.is_active = False # Le verrou natif de Django
            user.save()

            import logging
            logger = logging.getLogger('xcsm.auth')
            logger.info(f"Compte désactivé - User: {user.username}, Motif: {reason}")

            logout(request) # On termine la session actuelle

            return Response({
                "message": "Compte désactivé. Vos données restent disponibles mais l'accès est bloqué.",
                "reactivation": "Veuillez contacter le support pour une réactivation."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Erreur lors de la désactivation : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# SECTION 3 : RÉCUPÉRATION DE MOT DE PASSE (UC03)
# =============================================================================

class PasswordResetRequestView(generics.GenericAPIView):
    """
    Vue pour demander la réinitialisation du mot de passe.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = Utilisateur.objects.get(email=email)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Envoi de l'email
        reset_link = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password/{uid}/{token}/"
        
        try:
            send_mail(
                subject="[XCSM] Réinitialisation de votre mot de passe",
                message=f"Bonjour {user.username},\n\nUtilisez le lien suivant pour réinitialiser votre mot de passe (valide 1h) :\n{reset_link}\n\nSi vous n'avez pas demandé cette action, ignorez cet email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({"detail": "Un email de réinitialisation a été envoyé."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Erreur d'envoi.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Vue pour confirmer la réinitialisation.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Utilisateur.objects.get(pk=uid)
        except:
            return Response({"error": "Lien invalide."}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Mot de passe réinitialisé."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST)
