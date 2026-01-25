"""
Vues principales du projet XCSM.

Ce fichier contient les vues qui ne font pas partie de l'API REST
mais qui sont nécessaires pour le fonctionnement général du projet.
"""

from django.http import JsonResponse
from django.shortcuts import render

def home(request):
    """
    Vue de la page d'accueil du backend XCSM.
    
    Retourne une page d'accueil simple avec des informations sur l'API
    et des liens vers la documentation.
    
    Args:
        request: L'objet requête HTTP
        
    Returns:
        HttpResponse: Réponse HTML ou JSON selon l'en-tête Accept
    """
    # Vérifier si le client accepte JSON
    accept_header = request.META.get('HTTP_ACCEPT', '')

    if 'application/json' in accept_header or request.GET.get('format') == 'json':
        # Retourner une réponse JSON
        return JsonResponse({
            'project': 'XCSM Backend',
            'version': '1.0.0',
            'description': 'API de traitement et structuration de contenus pédagogiques',
            'documentation': {
                'swagger': request.build_absolute_uri('/swagger/'),
                'redoc': request.build_absolute_uri('/redoc/'),
                'api_root': request.build_absolute_uri('/api/v1/'),
            },
            'endpoints': {
                'authentication': request.build_absolute_uri('/api/v1/auth/'),
                'documents': request.build_absolute_uri('/api/v1/documents/'),
                'granules': request.build_absolute_uri('/api/v1/granules/'),
                'courses': request.build_absolute_uri('/api/v1/cours/'),
                'statistics': request.build_absolute_uri('/api/v1/statistics/'),
            },
            'status': 'operational',
            'maintainers': 'Team 4GI ENSP Promo 2027',
            'contact': 'xcsm.4gi.enspy.promo.2027@gmail.com',
        })

    # Sinon, retourner une page HTML simple
    context = {
        'project_name': 'XCSM Backend',
        'version': '1.0.0',
        'api_root': request.build_absolute_uri('/api/v1/'),
        'swagger_url': request.build_absolute_uri('/swagger/'),
        'redoc_url': request.build_absolute_uri('/redoc/'),
        'admin_url': request.build_absolute_uri('/admin/'),
    }

    return render(request, 'home.html', context)


def health_check(request):
    """
    Endpoint de vérification de santé (health check).
    
    Utilisé par les systèmes de monitoring pour vérifier que l'application
    est en cours d'exécution et fonctionne correctement.
    
    Args:
        request: L'objet requête HTTP
        
    Returns:
        JsonResponse: État de santé de l'application
    """
    from django.db import connection
    from django.core.cache import cache

    health_status = {
        'status': 'healthy',
        'timestamp': '2025-12-20T10:30:00Z',  # À remplacer par datetime réel
        'services': {},
        'version': '1.0.0',
    }

    # Vérifier la base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['services']['database'] = {
                'status': 'healthy',
                'type': 'MySQL',
                'response_time': 'OK'
            }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'

    # Vérifier le cache (si configuré)
    try:
        cache.set('health_check', 'test', 10)
        test_value = cache.get('health_check')
        health_status['services']['cache'] = {
            'status': 'healthy' if test_value == 'test' else 'unhealthy',
            'type': 'Redis' if hasattr(settings, 'REDIS_URL') else 'LocalMemory'
        }
    except Exception as e:
        health_status['services']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'

    # Ajouter des informations système
    import sys
    import platform

    health_status['system'] = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'django_version': '5.2.8',
    }

    return JsonResponse(health_status)


def api_root(request):
    """
    Point d'entrée racine de l'API.
    
    Fournit une vue d'ensemble de toutes les ressources API disponibles.
    
    Args:
        request: L'objet requête HTTP
        
    Returns:
        JsonResponse: Liste des endpoints disponibles
    """
    endpoints = {
        'authentication': {
            'login': request.build_absolute_uri('/api/v1/auth/login/'),
            'register': request.build_absolute_uri('/api/v1/auth/register/'),
            'profile': request.build_absolute_uri('/api/v1/auth/profile/'),
            'refresh': request.build_absolute_uri('/api/v1/auth/refresh/'),
            'logout': request.build_absolute_uri('/api/v1/auth/logout/'),
        },
        'documents': {
            'upload': request.build_absolute_uri('/api/v1/documents/upload/'),
            'json_structure': request.build_absolute_uri('/api/v1/documents/{id}/json/'),
        },
        'granules': {
            'detail': request.build_absolute_uri('/api/v1/granules/{id}/'),
            'search': request.build_absolute_uri('/api/v1/granules/search/'),
        },
        'courses': {
            'export': request.build_absolute_uri('/api/v1/cours/{id}/export-json/'),
        },
        'statistics': {
            'mongodb': request.build_absolute_uri('/api/v1/statistics/mongodb/'),
        },
        'documentation': {
            'swagger': request.build_absolute_uri('/swagger/'),
            'redoc': request.build_absolute_uri('/redoc/'),
            'schema': request.build_absolute_uri('/swagger.json'),
        },
        'system': {
            'health': request.build_absolute_uri('/health/'),
            'admin': request.build_absolute_uri('/admin/'),
        }
    }

    # Ajouter les endpoints de notifications si disponibles
    try:
        from xcsm import notifications
        endpoints['notifications'] = {
            'list': request.build_absolute_uri('/api/v1/notifications/'),
            'preferences': request.build_absolute_uri('/api/v1/notification-preferences/'),
            'push_subscriptions': request.build_absolute_uri('/api/v1/push-subscriptions/'),
        }
    except ImportError:
        pass

    return JsonResponse({
        'project': 'XCSM Backend API',
        'version': '1.0.0',
        'description': 'API REST pour le traitement et la structuration de contenus pédagogiques',
        'endpoints': endpoints,
        'formats': ['json'],
        'authentication': 'JWT Bearer Token',
        'rate_limiting': '1000 requests/hour per user',
        'contact': 'xcsm.4gi.enspy.promo.2027@gmail.com',
        'documentation': 'https://github.com/PafeDilane/XCSM_Backend',
    })