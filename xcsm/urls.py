"""
URLs de l'application XCSM avec authentification JWT et système de notifications.

Ce fichier configure toutes les routes de l'API XCSM, organisées en sections logiques.
Toutes les URLs sont préfixées par '/api/v1/' via l'inclusion dans xcsm_project/urls.py.

Organisation des endpoints :
- Authentification : /api/v1/auth/*
- Notifications : /api/v1/notifications/*
- Documents : /api/v1/documents/*
- Granules : /api/v1/granules/*
- Cours : /api/v1/cours/*
- Statistiques : /api/v1/statistics/*
"""

from django.conf import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import des vues d'authentification JWT
from .views_auth import (
    LoginView,
    RegisterView,
    RefreshTokenView,
    LogoutView,
    UserProfileView,
    ChangePasswordView,
    VerifyTokenView
)

# Import des vues principales (existant déjà)
from .views import (
    DocumentUploadView,
    FichierJsonStructureView,
    GranuleDetailView,
    CoursJsonExportView,
    GranuleSearchView,
    MongoStatisticsView
)

# Import des vues de notifications (si le module notifications existe)
try:
    from .notifications.views import (
        NotificationViewSet,
        NotificationPreferenceViewSet,
        PushSubscriptionViewSet,
        NotificationTemplateViewSet,
        NotificationDigestViewSet,
        BulkNotificationCreateView,
        NotificationStatsView
    )
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("⚠️  Module notifications non disponible - Les endpoints de notifications seront désactivés")

# =============================================================================
# ROUTER POUR LES VIEWSETS
# =============================================================================

# Création d'un router pour les ViewSets (meilleure organisation pour les CRUD)
router = DefaultRouter()

# Enregistrement des ViewSets de notifications (si disponibles)
if NOTIFICATIONS_AVAILABLE:
    router.register(r'notifications', NotificationViewSet, basename='notification')
    router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notificationpreference')
    router.register(r'push-subscriptions', PushSubscriptionViewSet, basename='pushsubscription')
    router.register(r'notification-templates', NotificationTemplateViewSet, basename='notificationtemplate')
    router.register(r'notification-digests', NotificationDigestViewSet, basename='notificationdigest')

# Note: Vous pouvez ajouter d'autres ViewSets ici à l'avenir
# Exemple: router.register(r'documents', DocumentViewSet, basename='document')

# =============================================================================
# LISTE DES URLS
# =============================================================================

urlpatterns = [
    # =========================================================================
    # SECTION 0 : AUTHENTIFICATION JWT
    # =========================================================================
    # Ces endpoints gèrent l'authentification des utilisateurs via JSON Web Tokens

    # POST /api/v1/auth/login/ - Connexion et obtention des tokens
    path('auth/login/', LoginView.as_view(), name='auth-login'),

    # POST /api/v1/auth/register/ - Inscription d'un nouvel utilisateur
    path('auth/register/', RegisterView.as_view(), name='auth-register'),

    # POST /api/v1/auth/refresh/ - Rafraîchissement d'un token expiré
    path('auth/refresh/', RefreshTokenView.as_view(), name='auth-refresh'),

    # POST /api/v1/auth/logout/ - Déconnexion et blacklist du refresh token
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),

    # GET/PUT /api/v1/auth/profile/ - Consultation et modification du profil
    path('auth/profile/', UserProfileView.as_view(), name='auth-profile'),

    # PUT /api/v1/auth/change-password/ - Changement de mot de passe
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # GET /api/v1/auth/verify/ - Vérification de la validité d'un token
    path('auth/verify/', VerifyTokenView.as_view(), name='auth-verify'),

    # =========================================================================
    # SECTION 1 : GESTION DES DOCUMENTS
    # =========================================================================
    # Ces endpoints permettent l'upload et la consultation des documents pédagogiques

    # POST /api/v1/documents/upload/ - Upload d'un nouveau document (PDF/DOCX)
    path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),

    # GET /api/v1/documents/<uuid:fichier_id>/json/ - Structure JSON d'un document traité
    path('documents/<uuid:fichier_id>/json/', FichierJsonStructureView.as_view(), name='fichier-json-structure'),

    # =========================================================================
    # SECTION 2 : CONSULTATION DES GRANULES
    # =========================================================================
    # Ces endpoints permettent d'accéder aux unités pédagogiques extraites

    # GET /api/v1/granules/<uuid:granule_id>/ - Détail d'un granule spécifique
    path('granules/<uuid:granule_id>/', GranuleDetailView.as_view(), name='granule-detail'),

    # GET /api/v1/granules/search/ - Recherche full-text dans les granules
    path('granules/search/', GranuleSearchView.as_view(), name='granule-search'),

    # =========================================================================
    # SECTION 3 : EXPORT ET CONSULTATION DES COURS
    # =========================================================================
    # Ces endpoints permettent d'exporter et de consulter les structures de cours

    # GET /api/v1/cours/<uuid:cours_id>/export-json/ - Export JSON complet d'un cours
    path('cours/<uuid:cours_id>/export-json/', CoursJsonExportView.as_view(), name='cours-json-export'),

    # =========================================================================
    # SECTION 4 : STATISTIQUES ET MONITORING
    # =========================================================================
    # Ces endpoints fournissent des métriques système (principalement pour les administrateurs)

    # GET /api/v1/statistics/mongodb/ - Statistiques de la base MongoDB
    path('statistics/mongodb/', MongoStatisticsView.as_view(), name='mongo-statistics'),
]

# =============================================================================
# INCLUSION DES URLS DES VIEWSETS (via router)
# =============================================================================

# Inclure les URLs générées par le router
# Cela ajoute automatiquement les endpoints CRUD pour les ViewSets enregistrés
urlpatterns += [
    path('', include(router.urls)),
]

# =============================================================================
# URLS SPÉCIFIQUES POUR LES NOTIFICATIONS (si disponibles)
# =============================================================================

if NOTIFICATIONS_AVAILABLE:
    urlpatterns += [
        # POST /api/v1/notifications/bulk/ - Création de notifications en masse
        path('notifications/bulk/', BulkNotificationCreateView.as_view(), name='bulk-notification-create'),

        # GET /api/v1/notifications/stats/ - Statistiques des notifications
        path('notifications/stats/', NotificationStatsView.as_view(), name='notification-stats'),
    ]

# =============================================================================
# URLS DE DÉVELOPPEMENT ET DEBUG
# =============================================================================

if settings.DEBUG:
    urlpatterns += [
        # Interface de test d'authentification fournie par DRF (utile pour le développement)
        path('auth/test/', include('rest_framework.urls')),
    ]

# =============================================================================
# DOCUMENTATION DES ENDPOINTS
# =============================================================================
"""
RÉSUMÉ DES ENDPOINTS DISPONIBLES :

AUTHENTIFICATION :
-----------------
POST   /api/v1/auth/login/          - Connexion
POST   /api/v1/auth/register/       - Inscription
POST   /api/v1/auth/refresh/        - Rafraîchissement token
POST   /api/v1/auth/logout/         - Déconnexion
GET    /api/v1/auth/profile/        - Profil utilisateur
PUT    /api/v1/auth/change-password/- Changement mot de passe
GET    /api/v1/auth/verify/         - Vérification token

DOCUMENTS :
-----------
POST   /api/v1/documents/upload/    - Upload document
GET    /api/v1/documents/{id}/json/ - Structure JSON

GRANULES :
----------
GET    /api/v1/granules/{id}/       - Détail granule
GET    /api/v1/granules/search/     - Recherche

COURS :
-------
GET    /api/v1/cours/{id}/export-json/ - Export JSON

STATISTIQUES :
--------------
GET    /api/v1/statistics/mongodb/  - Stats MongoDB

NOTIFICATIONS (si activé) :
---------------------------
GET    /api/v1/notifications/       - Liste notifications
POST   /api/v1/notifications/       - Créer notification
GET    /api/v1/notifications/{id}/  - Détail notification
PUT    /api/v1/notifications/{id}/  - Modifier notification
DELETE /api/v1/notifications/{id}/  - Supprimer notification
POST   /api/v1/notifications/mark-as-read/ - Marquer comme lues
POST   /api/v1/notifications/mark-all-read/ - Marquer toutes comme lues
GET    /api/v1/notifications/unread-count/ - Nombre non lues
GET    /api/v1/notifications/recent/ - Notifications récentes
POST   /api/v1/notifications/{id}/archive/ - Archiver notification

PRÉFÉRENCES NOTIFICATIONS :
---------------------------
GET    /api/v1/notification-preferences/ - Liste préférences
POST   /api/v1/notification-preferences/ - Créer préférences
GET    /api/v1/notification-preferences/{id}/ - Détail préférences
PUT    /api/v1/notification-preferences/{id}/ - Modifier préférences
DELETE /api/v1/notification-preferences/{id}/ - Supprimer préférences
GET    /api/v1/notification-preferences/mine/ - Mes préférences

ABONNEMENTS PUSH :
------------------
GET    /api/v1/push-subscriptions/  - Liste abonnements
POST   /api/v1/push-subscriptions/  - Créer abonnement
GET    /api/v1/push-subscriptions/{id}/ - Détail abonnement
PUT    /api/v1/push-subscriptions/{id}/ - Modifier abonnement
DELETE /api/v1/push-subscriptions/{id}/ - Supprimer abonnement
POST   /api/v1/push-subscriptions/unsubscribe/ - Désabonner appareil

TEMPLATES NOTIFICATIONS (admin) :
---------------------------------
GET    /api/v1/notification-templates/ - Liste templates
POST   /api/v1/notification-templates/ - Créer template
GET    /api/v1/notification-templates/{id}/ - Détail template
PUT    /api/v1/notification-templates/{id}/ - Modifier template
DELETE /api/v1/notification-templates/{id}/ - Supprimer template
POST   /api/v1/notification-templates/{id}/test/ - Tester template

SYNTHÈSES NOTIFICATIONS :
-------------------------
GET    /api/v1/notification-digests/ - Liste synthèses
GET    /api/v1/notification-digests/{id}/ - Détail synthèse

EN MASSE :
----------
POST   /api/v1/notifications/bulk/  - Créer notifications en masse

STATISTIQUES NOTIFICATIONS :
----------------------------
GET    /api/v1/notifications/stats/ - Statistiques notifications
"""