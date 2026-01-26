# # xcsm/serializers.py
# from rest_framework import serializers
# from .models import FichierSource

# class FichierSourceSerializer(serializers.ModelSerializer):

#     """ Sérialiseur pour la classe FichierSource (Upload) """
#     class Meta:
#         model = FichierSource
#         # Le frontend nous envoie le titre et le fichier
#         fields = ['titre', 'fichier_original']
#         read_only_fields = ['enseignant', 'statut_traitement', 'type_mime', 'mongo_transforme_id']









# xcsm/serializers.py
from rest_framework import serializers
from .models import FichierSource

class FichierSourceSerializer(serializers.ModelSerializer):
    """ Sérialiseur pour la classe FichierSource (Upload) """
    class Meta:
        model = FichierSource
        # Le frontend nous envoie le titre et le fichier
        fields = ['id', 'titre', 'fichier_original', 'date_upload', 'statut_traitement', 'mongo_transforme_id']
        # Champs protégés (gérés par le backend)
        read_only_fields = ['id', 'enseignant', 'date_upload', 'statut_traitement', 'type_mime', 'mongo_transforme_id']


"""
Serializers pour l'authentification JWT
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password

from .models import Utilisateur, Enseignant, Etudiant, Administrateur


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé pour les tokens JWT avec infos XCSM
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Informations de base
        token['user_id'] = str(user.id)
        token['username'] = user.username
        token['email'] = user.email
        token['type_compte'] = user.type_compte
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name

        # Informations spécifiques au rôle
        try:
            if user.type_compte == 'ENSEIGNANT':
                enseignant = user.profil_enseignant
                token['enseignant_id'] = str(enseignant.utilisateur.id)
                token['specialite'] = enseignant.specialite
                token['departement'] = enseignant.departement
            elif user.type_compte == 'ETUDIANT':
                etudiant = user.profil_etudiant
                token['etudiant_id'] = str(etudiant.utilisateur.id)
                token['matricule'] = etudiant.matricule
                token['niveau'] = etudiant.niveau
                token['filiere'] = etudiant.filiere
            elif user.type_compte == 'ADMIN':
                admin = user.profil_admin
                token['admin_id'] = str(admin.utilisateur.id)
                token['role_admin'] = admin.role_admin
        except:
            pass

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Construction de la réponse personnalisée
        data['user'] = {
            'id': str(self.user.id),
            'username': self.user.username,
            'email': self.user.email,
            'type_compte': self.user.type_compte,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'photo_url': self.user.photo_url.url if self.user.photo_url else None,
        }

        # Ajout des informations de profil
        try:
            if self.user.type_compte == 'ENSEIGNANT':
                enseignant = self.user.profil_enseignant
                data['user']['enseignant'] = {
                    'specialite': enseignant.specialite,
                    'departement': enseignant.departement
                }
            elif self.user.type_compte == 'ETUDIANT':
                etudiant = self.user.profil_etudiant
                data['user']['etudiant'] = {
                    'matricule': etudiant.matricule,
                    'niveau': etudiant.niveau,
                    'filiere': etudiant.filiere
                }
            elif self.user.type_compte == 'ADMIN':
                admin = self.user.profil_admin
                data['user']['admin'] = {
                    'role_admin': admin.role_admin,
                    'permissions': admin.permissions
                }
        except:
            pass

        return data


from .models import Utilisateur, Enseignant, Etudiant, Administrateur, Cours, ActionLog, Evaluation, Correction

class ActionLogSerializer(serializers.ModelSerializer):
    # ... (existing content)
    utilisateur_username = serializers.CharField(source='utilisateur.username', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = ActionLog
        fields = ('id', 'utilisateur_username', 'action_type', 'action_type_display', 'description', 'timestamp', 'metadata')
        read_only_fields = ('id', 'timestamp')


class EvaluationSerializer(serializers.ModelSerializer):
    # ...
    class Meta:
        model = Evaluation
        fields = '__all__'
        read_only_fields = ('id', 'date_creation')

class CoursSerializer(serializers.ModelSerializer):
    """ Serializer pour les cours (Squelette pédagogique) """
    class Meta:
        model = Cours
        fields = '__all__'
        read_only_fields = ('id', 'date_creation')

class CorrectionSerializer(serializers.ModelSerializer):
    """ Serializer pour les corrections """
    class Meta:
        model = Correction
        fields = '__all__'
        read_only_fields = ('id', 'date_creation')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription des utilisateurs
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Utilisateur
        fields = (
            'id', 'username', 'email', 'password', 'confirm_password',
            'type_compte', 'first_name', 'last_name', 'photo_url'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True},
        }

    def validate(self, data):
        """
        Validation des données d'inscription
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )

        if Utilisateur.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Cet email est déjà utilisé."}
            )

        if Utilisateur.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError(
                {"username": "Ce nom d'utilisateur est déjà utilisé."}
            )

        return data

    def create(self, validated_data):
        """
        Création d'un utilisateur avec son type de compte
        """
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        type_compte = validated_data.pop('type_compte')

        # Création de l'utilisateur
        user = self.Meta.model.objects.create_user(
            **validated_data,
            password=password,
            type_compte=type_compte,
            is_active=True
        )

        # Création du profil spécifique
        if type_compte == 'ENSEIGNANT':
            from .models import Enseignant
            Enseignant.objects.create(
                utilisateur=user,
                specialite="À définir",
                departement="À définir"
            )
        elif type_compte == 'ETUDIANT':
            from .models import Etudiant
            Etudiant.objects.create(
                utilisateur=user,
                matricule="À définir",
                niveau="À définir",
                filiere="À définir"
            )
        elif type_compte == 'ADMIN':
            from .models import Administrateur
            Administrateur.objects.create(
                utilisateur=user,
                role_admin="Administrateur",
                permissions="{}"
            )

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur
    """
    full_name = serializers.SerializerMethodField()
    profile_complete = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'type_compte', 'photo_url', 'date_creation',
            'last_login', 'profile_complete'
        )
        read_only_fields = ('id', 'username', 'type_compte', 'date_creation')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_profile_complete(self, obj):
        try:
            if obj.type_compte == 'ENSEIGNANT':
                profile = obj.profil_enseignant
                return all([profile.specialite, profile.departement])
            elif obj.type_compte == 'ETUDIANT':
                profile = obj.profil_etudiant
                return all([profile.matricule, profile.niveau, profile.filiere])
            elif obj.type_compte == 'ADMIN':
                return True
        except:
            return False
        return False


class EnseignantProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil enseignant
    """
    class Meta:
        model = Enseignant
        fields = ('specialite', 'departement')


class EtudiantProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil étudiant
    """
    class Meta:
        model = Etudiant
        fields = ('matricule', 'niveau', 'filiere')


class AdministrateurProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil administrateur
    """
    class Meta:
        model = Administrateur
        fields = ('role_admin', 'permissions')


class AccountDeletionSerializer(serializers.Serializer):
    """
    Serializer pour la validation de la suppression de compte.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Mot de passe actuel pour confirmation"
    )

    confirmation = serializers.CharField(
        required=True,
        help_text="Écrivez 'JE_SUPPRIME_MON_COMPTE' pour confirmer"
    )

    def validate_confirmation(self, value):
        """
        Valide la phrase de confirmation.
        """
        if value != "JE_SUPPRIME_MON_COMPTE":
            raise serializers.ValidationError(
                "Vous devez écrire exactement 'JE_SUPPRIME_MON_COMPTE' pour confirmer la suppression."
            )
        return value


class AccountDeactivationSerializer(serializers.Serializer):
    """
    Serializer pour la validation de la désactivation de compte.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Mot de passe actuel pour confirmation"
    )

    reason = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Raison de la désactivation (optionnel)"
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer pour la demande de réinitialisation de mot de passe.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not Utilisateur.objects.filter(email=value).exists():
            # Pour la sécurité, on pourrait ne pas lever d'erreur ici pour éviter l'énumération,
            # mais le spec UC03 4a dit "Email introuvable".
            raise serializers.ValidationError("Cet email ne correspond à aucun compte.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer pour la confirmation du nouveau mot de passe avec token.
    """
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "Les mots de passe ne correspondent pas."})
        
        # Validation complexité (UC01 Rules)
        password = data['new_password']
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError({"new_password": "Le mot de passe doit contenir au moins un chiffre."})
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError({"new_password": "Le mot de passe doit contenir au moins une majuscule."})
            
        return data