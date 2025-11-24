# xcsm/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Utilisateur, Enseignant, Etudiant, Administrateur, FichierSource

# ====================================================================
# 1. CLASSES ADMIN POUR AFFICHAGE OPTIMISÉ
# ====================================================================

# Admin personnalisé pour le modèle Utilisateur (hérite des fonctionnalités de BaseUserAdmin)
class UtilisateurAdmin(BaseUserAdmin):
    # Champs affichés dans la liste d'aperçu de l'utilisateur
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'type_compte')
    
    # Ajout des champs spécifiques à notre modèle dans le formulaire d'édition
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Supplémentaires XCSM', {'fields': ('photo_url', 'type_compte')}),
    )

# Admin simple pour les profils métiers (pour la lisibilité)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'specialite', 'departement')
    search_fields = ('utilisateur__username', 'specialite')

class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'matricule', 'niveau', 'filiere')
    search_fields = ('matricule', 'utilisateur__username')

class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'role_admin')

class FichierSourceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'enseignant', 'date_upload', 'statut_traitement')
    list_filter = ('statut_traitement', 'date_upload')
    search_fields = ('titre', 'enseignant__utilisateur__username')


# ====================================================================
# 2. ENREGISTREMENT DES MODÈLES (CRITIQUE pour le 404)
# ====================================================================
admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Enseignant, EnseignantAdmin)
admin.site.register(Etudiant, EtudiantAdmin)
admin.site.register(Administrateur, AdministrateurAdmin)
admin.site.register(FichierSource, FichierSourceAdmin)