"""
Personnalisation des tokens JWT pour inclure les informations spécifiques XCSM
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé pour ajouter des informations spécifiques au token JWT

    Inclut automatiquement dans le token :
    - L'ID utilisateur
    - Le type de compte (role)
    - L'username
    - L'email
    - Le profil enseignant/étudiant/admin si existant
    """

    @classmethod
    def get_token(cls, user):
        """
        Crée un token JWT personnalisé avec les informations XCSM
        """
        token = super().get_token(user)

        # Informations de base
        token['user_id'] = str(user.id)
        token['username'] = user.username
        token['email'] = user.email
        token['type_compte'] = user.type_compte

        # Informations spécifiques au rôle
        if user.type_compte == 'ENSEIGNANT':
            try:
                enseignant = user.profil_enseignant
                token['enseignant_id'] = str(enseignant.utilisateur.id)
                token['specialite'] = enseignant.specialite
                token['departement'] = enseignant.departement
            except:
                pass

        elif user.type_compte == 'ETUDIANT':
            try:
                etudiant = user.profil_etudiant
                token['etudiant_id'] = str(etudiant.utilisateur.id)
                token['matricule'] = etudiant.matricule
                token['niveau'] = etudiant.niveau
                token['filiere'] = etudiant.filiere
            except:
                pass

        elif user.type_compte == 'ADMIN':
            try:
                admin = user.profil_admin
                token['admin_id'] = str(admin.utilisateur.id)
                token['role_admin'] = admin.role_admin
            except:
                pass

        return token

    def validate(self, attrs):
        """
        Validation personnalisée avec vérification du type de compte
        """
        data = super().validate(attrs)

        # Ajout des informations supplémentaires dans la réponse
        refresh = self.get_token(self.user)

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

        # Ajout des informations spécifiques au profil
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
            # Si le profil n'existe pas encore
            pass

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vue personnalisée utilisant notre serializer JWT
    """
    serializer_class = CustomTokenObtainPairSerializer


# Serializer pour l'inscription
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription des utilisateurs
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    type_compte = serializers.ChoiceField(choices=[('ENSEIGNANT', 'Enseignant'), ('ETUDIANT', 'Étudiant'), ('ADMIN', 'Administrateur')])

    class Meta:
        from .models import Utilisateur
        model = Utilisateur
        fields = ('username', 'email', 'password', 'confirm_password', 'type_compte',
                  'first_name', 'last_name')

    def validate(self, data):
        """
        Validation des données d'inscription
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})

        # Validation email unique
        if self.Meta.model.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Cet email est déjà utilisé."})

        # Validation username unique
        if self.Meta.model.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Ce nom d'utilisateur est déjà utilisé."})

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
            type_compte=type_compte
        )

        # Création du profil spécifique (à compléter selon le type)
        # Note: Cette partie pourrait être déplacée dans un signal
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
                matricule=f"ETU-{str(user.id)[:8].upper()}",
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