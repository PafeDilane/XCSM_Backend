# xcsm/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# ==============================================================================
# BLOC ACTEURS (UTILISATEURS) - Conforme au Diagramme de Classe D_Classe.jpg
# ==============================================================================

class Utilisateur(AbstractUser):
    """
    Classe Mère correspondante à 'Utilisateur' sur le diagramme.
    Hérite d'AbstractUser pour la gestion sécu (mot de passe, login, is_active).
    """
    # Attributs du Diagramme
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # email, password, nom, prenom, date_creation, last_login, is_active sont gérés par AbstractUser
    
    photo_url = models.ImageField(upload_to='photos_profil/', null=True, blank=True, verbose_name="Photo URL")
    
    # Champs de timestamps explicites si le diagramme les demande distinctement de Django
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date Création")
    derniere_connexion = models.DateTimeField(null=True, blank=True, verbose_name="Dernière Connexion")

    # Rôle pour faciliter le typage (même si on a des tables filles)
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('ENSEIGNANT', 'Enseignant'),
        ('ETUDIANT', 'Etudiant'),
    )
    type_compte = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Type de Compte")

    def __str__(self):
        return f"{self.username}"

class Enseignant(models.Model):
    """
    Classe Fille : Enseignant
    """
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True, related_name='profil_enseignant')
    
    # Attributs spécifiques du Diagramme
    specialite = models.CharField(max_length=100, verbose_name="Spécialité")
    departement = models.CharField(max_length=100, verbose_name="Département")

    def __str__(self):
        return f"Ens. {self.utilisateur.last_name} ({self.specialite})"

class Etudiant(models.Model):
    """
    Classe Fille : Etudiant
    """
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True, related_name='profil_etudiant')
    
    # Attributs spécifiques du Diagramme
    matricule = models.CharField(max_length=50, unique=True, verbose_name="Matricule")
    niveau = models.CharField(max_length=50, verbose_name="Niveau")
    filiere = models.CharField(max_length=100, verbose_name="Filière")

    def __str__(self):
        return f"Etu. {self.matricule}"

class Administrateur(models.Model):
    """
    Classe Fille : Administrateur
    """
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True, related_name='profil_admin')
    
    # Attributs spécifiques du Diagramme
    role_admin = models.CharField(max_length=100, verbose_name="Rôle Admin") # Ex: SuperAdmin, Moderateur
    permissions = models.TextField(null=True, blank=True, verbose_name="Liste Permissions") # Stockage simple ou JSON

    def __str__(self):
        return f"Admin {self.utilisateur.username}"