# xcsm/utils.py
import logging
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)

def get_mongo_db():
    """
    Retourne une instance de la base de données MongoDB sécurisée avec timeout.
    """
    try:
        # On définit un timeout court (3s) pour éviter de bloquer l'API si Mongo est KO
        client = MongoClient(
            'mongodb://localhost:27017/',
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=2000
        )
        
        # Test de connexion immédiat
        client.server_info()
        
        return client['xcsm_granules_db']
    except Exception as e:
        logger.critical(f"❌ Impossible de se connecter à MongoDB : {e}")
        # On lève une erreur explicite qui sera attrapée par notre Custom Exception Handler
        raise ConnectionError("Le service de stockage sémantique (MongoDB) est actuellement indisponible.")