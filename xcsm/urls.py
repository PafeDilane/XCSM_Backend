"""
URLs de l'application XCSM avec authentification JWT
"""
from django.conf import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_auth import (
    LoginView,
    RegisterView,
    RefreshTokenView,
    LogoutView,
    UserProfileView,
    ChangePasswordView,
    VerifyTokenView
)
from .views import (
    DocumentUploadView,
    FichierJsonStructureView,
    GranuleDetailView,
    CoursJsonExportView,
    GranuleSearchView,
    MongoStatisticsView
)

# Router pour les vues ViewSet (si besoin future)
router = DefaultRouter()
# router.register('documents', DocumentViewSet, basename='document')

urlpatterns = [
    # =========================================================================
    # 0. AUTHENTIFICATION JWT
    # =========================================================================

    # Connexion
    path(
        'auth/login/',
        LoginView.as_view(),
        name='auth-login'
    ),

    # Inscription
    path(
        'auth/register/',
        RegisterView.as_view(),
        name='auth-register'
    ),

    # Rafraîchissement token
    path(
        'auth/refresh/',
        RefreshTokenView.as_view(),
        name='auth-refresh'
    ),

    # Déconnexion
    path(
        'auth/logout/',
        LogoutView.as_view(),
        name='auth-logout'
    ),

    # Profil utilisateur
    path(
        'auth/profile/',
        UserProfileView.as_view(),
        name='auth-profile'
    ),

    # Changement mot de passe
    path(
        'auth/change-password/',
        ChangePasswordView.as_view(),
        name='auth-change-password'
    ),

    # Vérification token
    path(
        'auth/verify/',
        VerifyTokenView.as_view(),
        name='auth-verify'
    ),

    # =========================================================================
    # 1. GESTION DES DOCUMENTS
    # =========================================================================

    # Upload de document
    path(
        'documents/upload/',
        DocumentUploadView.as_view(),
        name='document-upload'
    ),

    # Structure JSON d'un document
    path(
        'documents/<uuid:fichier_id>/json/',
        FichierJsonStructureView.as_view(),
        name='fichier-json-structure'
    ),

    # =========================================================================
    # 2. CONSULTATION DES GRANULES
    # =========================================================================

    # Détail d'un granule
    path(
        'granules/<uuid:granule_id>/',
        GranuleDetailView.as_view(),
        name='granule-detail'
    ),

    # Recherche dans les granules
    path(
        'granules/search/',
        GranuleSearchView.as_view(),
        name='granule-search'
    ),

    # =========================================================================
    # 3. EXPORT ET CONSULTATION DES COURS
    # =========================================================================

    # Export JSON d'un cours
    path(
        'cours/<uuid:cours_id>/export-json/',
        CoursJsonExportView.as_view(),
        name='cours-json-export'
    ),

    # =========================================================================
    # 4. STATISTIQUES ET MONITORING
    # =========================================================================

    # Statistiques MongoDB
    path(
        'statistics/mongodb/',
        MongoStatisticsView.as_view(),
        name='mongo-statistics'
    ),

    # =========================================================================
    # 5. ROUTER POUR LES VIEWSETS (optionnel)
    # =========================================================================
    # path('', include(router.urls)),
]

# URLs de debug (seulement en développement)
if settings.DEBUG:
    urlpatterns += [
        path('auth/test/', include('rest_framework.urls')),
    ]