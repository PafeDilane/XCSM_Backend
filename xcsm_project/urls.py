"""
Configuration des URLs pour le projet xcsm_project.

La liste `urlpatterns` route les URLs vers les vues. Pour plus d'informations, voir :
    https://docs.djangoproject.com/fr/5.2/topics/http/urls/

Exemples :
Vues fonctions
    1. Ajouter une importation :  from my_app import views
    2. Ajouter une URL à urlpatterns :  path('', views.home, name='home')

Vues basées sur les classes
    1. Ajouter une importation :  from other_app.views import Home
    2. Ajouter une URL à urlpatterns :  path('', Home.as_view(), name='home')

Inclusion d'une autre configuration d'URL
    1. Importer la fonction include() : from django.urls import include, path
    2. Ajouter une URL à urlpatterns :  path('blog/', include('blog.urls'))

English version:
URL configuration for xcsm_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')

Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import de la vue de la page d'accueil
from xcsm_project.views import home

# ------------------------------------------------------------
# CONFIGURATION DE SWAGGER / DOCUMENTATION API
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
   # Page d'accueil
   # --------------------------------------------------------
   path('', home, name='home'),

   # --------------------------------------------------------
   # Interface d'administration Django
   # --------------------------------------------------------
   path('admin/', admin.site.urls),

   # --------------------------------------------------------
   # URLs de l'application métier (xcsm) sous le préfixe API v1
   # --------------------------------------------------------
   path('api/v1/', include('xcsm.urls')),

   # --------------------------------------------------------
   # Documentation interactive de l'API
   # --------------------------------------------------------
   # JSON/YAML
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   # Format JSON simple (pour compatibilité)
   path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json-simple'),
   # Swagger UI
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   # Redoc
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# ------------------------------------------------------------
# Servir les fichiers médias (documents bruts) en développement
# ------------------------------------------------------------
if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

   # Debug toolbar (seulement en développement si installée)
   try:
      import debug_toolbar
      urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
   except ImportError:
      pass