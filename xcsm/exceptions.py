from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions global pour XCSM.
    Attrape TOUTES les erreurs, même les plus inattendues (Crash DB, Out of Memory, etc.)
    et renvoie une réponse JSON standardisée à l'examinateur.
    """
    # On appelle d'abord le gestionnaire par défaut de DRF
    response = exception_handler(exc, context)

    # Si response est None, c'est une erreur non gérée par DRF (ex: ConnectionError, ValueError)
    if response is None:
        logger.error(f"💥 CRASH INATTENDU : {str(exc)} | Context: {context}", exc_info=True)
        
        error_payload = {
            "error": "Erreur Interne du Serveur",
            "message": "Une erreur technique est survenue. L'équipe a été notifiée.",
            "technical_detail": str(exc) if hasattr(exc, '__str__') else "Inconnu",
            "status_code": 500
        }
        
        # Cas particuliers (Bases de données)
        if "ConnectionError" in str(type(exc)) or "OperationalError" in str(type(exc)):
            error_payload["error"] = "Service Indisponible"
            error_payload["message"] = "La base de données ou un service tiers ne répond pas."
            return Response(error_payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(error_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Si c'est une erreur DRF standard (401, 403, 404, Validation), on uniformise le format
    custom_data = {
        "error": response.status_text,
        "details": response.data,
        "status_code": response.status_code
    }
    response.data = custom_data

    return response
