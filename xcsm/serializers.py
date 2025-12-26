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
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        user = Utilisateur.objects.create_user(
            **validated_data,
            password=password
        )

        # Création du profil spécifique
        if user.type_compte == 'ENSEIGNANT':
            Enseignant.objects.create(
                utilisateur=user,
                specialite="À définir",
                departement="À définir"
            )
        elif user.type_compte == 'ETUDIANT':
            Etudiant.objects.create(
                utilisateur=user,
                matricule=f"ETU-{str(user.id)[:8].upper()}",
                niveau="À définir",
                filiere="À définir"
            )
        elif user.type_compte == 'ADMIN':
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