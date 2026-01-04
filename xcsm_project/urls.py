"""
URL configuration for xcsm_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import des vues du projet
from xcsm_project.views import home, health_check, api_root

# ------------------------------------------------------------
# CONFIGURATION DE LA DOCUMENTATION API
# ------------------------------------------------------------
schema_view = get_schema_view(
   openapi.Info(
      title="XCSM Backend API",
      default_version='v1',
      description="API de traitement et structuration de contenus pédagogiques",
      terms_of_service="https://xcsm.edu/terms/",
      contact=openapi.Contact(email="contact@xcsm.edu"),
      license=openapi.License(name="Academic License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

# ------------------------------------------------------------
# LISTE DES URLS DU PROJET
# ------------------------------------------------------------
urlpatterns = [
   # --------------------------------------------------------
   # Pages principales
   # --------------------------------------------------------

   # Page d'accueil
   path('', home, name='home'),

   # Health check pour le monitoring
   path('health/', health_check, name='health-check'),

   # Racine de l'API
   path('api/', api_root, name='api-root'),

   # --------------------------------------------------------
   # Administration
   # --------------------------------------------------------

   # Interface d'administration Django
   path('admin/', admin.site.urls),

   # --------------------------------------------------------
   # API XCSM v1
   # --------------------------------------------------------

   # Toutes les URLs de l'application XCSM sont préfixées par /api/v1/
   path('api/v1/', include('xcsm.urls')),

   # --------------------------------------------------------
   # Documentation de l'API
   # --------------------------------------------------------

   # Schema OpenAPI au format JSON/YAML
   re_path(r'^swagger(?P<format>\.json|\.yaml)$',
           schema_view.without_ui(cache_timeout=0),
           name='schema-json'),

   # Format JSON simple (compatibilité)
   path('swagger.json',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json-simple'),

   # Interface Swagger UI interactive
   path('swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),

   # Documentation Redoc
   path('redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'),
]

# ------------------------------------------------------------
# CONFIGURATION POUR LE DÉVELOPPEMENT
# ------------------------------------------------------------
if settings.DEBUG:
   # Servir les fichiers médias (documents uploadés)
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

   # Servir les fichiers statiques
   urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

   # Debug toolbar (uniquement si installée)
   try:
      import debug_toolbar
      urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
   except ImportError:
      pass