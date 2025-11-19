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




# ==============================================================================
# 2. BLOC RESSOURCES (LOGIQUE MODIFIÉE : PONT VERS MONGODB)
# ==============================================================================

class FichierSource(models.Model):
    """
    Représente le fichier PDF uploadé par l'enseignant.
    Sert de référence vers la version 'manipulable' (HTML/XML) stockée dans MongoDB.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name="mes_fichiers")
    
    # Métadonnées MySQL
    titre = models.CharField(max_length=255, verbose_name="Titre du document")
    
    # Le fichier brut original (PDF) est gardé sur le disque pour archivage/téléchargement
    fichier_original = models.FileField(upload_to='documents_bruts/', verbose_name="PDF Original")
    
    # CLÉ CRITIQUE VERS MONGODB (Collection "Fichiers Uploades")
    # Une fois le PDF transformé en HTML/XML, on stocke son ID Mongo ici.
    mongo_transforme_id = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        help_text="ID du document transformé (HTML/XML) dans la collection MongoDB 'Fichiers Uploades'"
    )
    
    statut_traitement = models.CharField(
        max_length=20, 
        choices=[('EN_ATTENTE', 'En attente'), ('TRAITE', 'Traité'), ('ERREUR', 'Erreur')],
        default='EN_ATTENTE'
    )
    
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} ({self.statut_traitement})"

# ==============================================================================
# 3. BLOC STRUCTURE PÉDAGOGIQUE (Inchangé, c'est le squelette)
# ==============================================================================

class Cours(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name="mes_cours")
    titre = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='cours_images/', null=True, blank=True)
    est_publie = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

class Partie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="parties")
    titre = models.CharField(max_length=200)
    numero = models.PositiveIntegerField()

    class Meta: ordering = ['numero']

class Chapitre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partie = models.ForeignKey(Partie, on_delete=models.CASCADE, related_name="chapitres")
    titre = models.CharField(max_length=200)
    numero = models.PositiveIntegerField()

    class Meta: ordering = ['numero']

class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapitre = models.ForeignKey(Chapitre, on_delete=models.CASCADE, related_name="sections")
    titre = models.CharField(max_length=200)
    numero = models.PositiveIntegerField()

    class Meta: ordering = ['numero']

class SousSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="sous_sections")
    titre = models.CharField(max_length=200)
    numero = models.PositiveIntegerField()

    class Meta: ordering = ['numero']

# ==============================================================================
# 4. LE GRANULE (EXTRAIT DU FICHIER TRANSFORMÉ)
# ==============================================================================

class Granule(models.Model):
    """
    Unité atomique extraite du fichier transformé.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sous_section = models.ForeignKey(SousSection, on_delete=models.CASCADE, related_name="granules")
    
    # Lien vers le fichier source transformé (La référence dont tu parlais)
    fichier_source = models.ForeignKey(FichierSource, on_delete=models.CASCADE, related_name="granules_extraits")
    
    titre = models.CharField(max_length=255)
    type_contenu = models.CharField(max_length=50, default='TEXTE')
    
    # ID du contenu spécifique (le petit bout de texte/html) dans la collection "Granules" de MongoDB
    mongo_contenu_id = models.CharField(max_length=100, help_text="ID du fragment dans MongoDB")
    
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return self.titre