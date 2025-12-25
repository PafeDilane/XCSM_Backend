 # # xcsm/urls.py
# from django.urls import path
# from .views import DocumentUploadView

# urlpatterns = [
#     path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),

# ]




# # xcsm/urls.py
# from django.urls import path
# from .views import DocumentUploadView

# urlpatterns = [
#     path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),
# ]

# xcsm/urls.py - Configuration complète des endpoints
from django.urls import path
from .views import (
    DocumentUploadView,
    FichierJsonStructureView,
    GranuleDetailView,
    CoursJsonExportView,
    GranuleSearchView,
    MongoStatisticsView
)

urlpatterns = [
    # =========================================================================
    # 1. GESTION DES DOCUMENTS
    # =========================================================================
    
    # Upload d'un nouveau document (PDF/DOCX)
    path(
        'documents/upload/', 
        DocumentUploadView.as_view(), 
        name='document-upload'
    ),
    
    # Consultation de la structure JSON d'un fichier
    path(
        'documents/<uuid:fichier_id>/json/', 
        FichierJsonStructureView.as_view(), 
        name='fichier-json-structure'
    ),
    
    # =========================================================================
    # 2. CONSULTATION DES GRANULES
    # =========================================================================
    
    # Détail d'un granule spécifique
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
    
    # Export complet d'un cours en JSON
    path(
        'cours/<uuid:cours_id>/export-json/', 
        CoursJsonExportView.as_view(), 
        name='cours-json-export'
    ),
    
    # =========================================================================
    # 4. STATISTIQUES ET MONITORING
    # =========================================================================
    
    # Statistiques MongoDB (admin uniquement)
    path(
        'statistics/mongodb/', 
        MongoStatisticsView.as_view(), 
        name='mongo-statistics'
    ),
]