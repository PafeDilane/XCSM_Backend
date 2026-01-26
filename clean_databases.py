import os
import django
from pymongo import MongoClient

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xcsm_project.settings')
django.setup()

def clean_mongodb():
    print("🧹 Nettoyage de MongoDB...")
    try:
        from xcsm.utils import get_mongo_db
        db = get_mongo_db()
        # Supprimer les collections pour repartir de zéro
        db.granules.delete_many({})
        db.fichiers_uploades.delete_many({})
        print("✅ Collections MongoDB vidées.")
    except Exception as e:
        print(f"⚠️ Erreur MongoDB lors du nettoyage : {e}")

if __name__ == "__main__":
    clean_mongodb()
