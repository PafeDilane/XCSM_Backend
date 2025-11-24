# xcsm/processing.py
import fitz  # PyMuPDF
from .utils import get_mongo_db
from django.db import transaction

def pdf_to_html_pymupdf(file_path):
    """
    Extrait le contenu d'un PDF en une structure HTML simple pour manipulation.
    C'est le module d'extraction initial.
    """
    document = fitz.open(file_path)
    html_content = ""
    
    # Parcourt les pages et extrait le texte avec les propriétés de mise en page
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        
        # Le format 'html' est le plus simple pour obtenir une structure de texte riche
        text_as_html = page.get_text("html")
        
        # On encapsule chaque page (facilite le découpage par la suite)
        html_content += f"<div class='page' data-page='{page_num + 1}'>{text_as_html}</div>"
        
    return f"<html><body>{html_content}</body></html>"

def process_and_store_document(fichier_source_instance):
    """
    Pipeline de Traitement : Lit PDF, convertit, stocke dans MongoDB.
    """
    # 1. Chemin d'accès au fichier enregistré (MEDIA_ROOT)
    file_path = fichier_source_instance.fichier_original.path
    
    try:
        # 2. Transformation (Extraction)
        transformed_content = pdf_to_html_pymupdf(file_path)
        
        # 3. Stockage dans MongoDB (Collection "Fichiers Uploades")
        mongo_db = get_mongo_db()
        fichiers_collection = mongo_db['fichiers_uploades'] # Ta collection de référence
        
        mongo_document = {
            "fichier_source_id": str(fichier_source_instance.id),
            "titre": fichier_source_instance.titre,
            "type_original": fichier_source_instance.fichier_original.name.split('.')[-1].upper(),
            "contenu_transforme": transformed_content, # Le contenu HTML structuré
            "date_traitement": fichier_source_instance.date_upload.isoformat()
        }
        
        result = fichiers_collection.insert_one(mongo_document)
        mongo_id = str(result.inserted_id)
        
        # 4. Mise à jour de l'instance MySQL (statut traité)
        with transaction.atomic():
            fichier_source_instance.mongo_transforme_id = mongo_id
            fichier_source_instance.statut_traitement = 'TRAITE'
            fichier_source_instance.type_mime = 'text/html' # Le type de la transformation
            fichier_source_instance.save()
        
        return True, "Fichier traité et stocké dans MongoDB."
        
    except Exception as e:
        # En cas d'erreur (ex: PDF corrompu, problème MongoDB)
        print(f"Erreur lors du traitement du document: {e}")
        with transaction.atomic():
            fichier_source_instance.statut_traitement = 'ERREUR'
            fichier_source_instance.save()
        return False, str(e)

# Note: En production, 'process_and_store_document' doit être ASYNCHRONE (Celery)
# pour ne pas forcer l'utilisateur à attendre 30s.