# xcsm/processing.py
# import fitz  # PyMuPDF
# from .utils import get_mongo_db
# from django.db import transaction

# def pdf_to_html_pymupdf(file_path):
#     """
#     Extrait le contenu d'un PDF en une structure HTML simple pour manipulation.
#     C'est le module d'extraction initial.
#     """
#     document = fitz.open(file_path)
#     html_content = ""
    
#     # Parcourt les pages et extrait le texte avec les propriétés de mise en page
#     for page_num in range(len(document)):
#         page = document.load_page(page_num)
        
#         # Le format 'html' est le plus simple pour obtenir une structure de texte riche
#         text_as_html = page.get_text("html")
        
#         # On encapsule chaque page (facilite le découpage par la suite)
#         html_content += f"<div class='page' data-page='{page_num + 1}'>{text_as_html}</div>"
        
#     return f"<html><body>{html_content}</body></html>"

# def process_and_store_document(fichier_source_instance):
#     """
#     Pipeline de Traitement : Lit PDF, convertit, stocke dans MongoDB.
#     """
#     # 1. Chemin d'accès au fichier enregistré (MEDIA_ROOT)
#     file_path = fichier_source_instance.fichier_original.path
    
#     try:
#         # 2. Transformation (Extraction)
#         transformed_content = pdf_to_html_pymupdf(file_path)
        
#         # 3. Stockage dans MongoDB (Collection "Fichiers Uploades")
#         mongo_db = get_mongo_db()
#         fichiers_collection = mongo_db['fichiers_uploades'] # Ta collection de référence
        
#         mongo_document = {
#             "fichier_source_id": str(fichier_source_instance.id),
#             "titre": fichier_source_instance.titre,
#             "type_original": fichier_source_instance.fichier_original.name.split('.')[-1].upper(),
#             "contenu_transforme": transformed_content, # Le contenu HTML structuré
#             "date_traitement": fichier_source_instance.date_upload.isoformat()
#         }
        
#         result = fichiers_collection.insert_one(mongo_document)
#         mongo_id = str(result.inserted_id)
        
#         # 4. Mise à jour de l'instance MySQL (statut traité)
#         with transaction.atomic():
#             fichier_source_instance.mongo_transforme_id = mongo_id
#             fichier_source_instance.statut_traitement = 'TRAITE'
#             fichier_source_instance.type_mime = 'text/html' # Le type de la transformation
#             fichier_source_instance.save()
        
#         return True, "Fichier traité et stocké dans MongoDB."
        
#     except Exception as e:
#         # En cas d'erreur (ex: PDF corrompu, problème MongoDB)
#         print(f"Erreur lors du traitement du document: {e}")
#         with transaction.atomic():
#             fichier_source_instance.statut_traitement = 'ERREUR'
#             fichier_source_instance.save()
#         return False, str(e)

# # Note: En production, 'process_and_store_document' doit être ASYNCHRONE (Celery)
# # pour ne pas forcer l'utilisateur à attendre 30s.



# # xcsm/processing.py
# import fitz  # PyMuPDF pour PDF
# from docx import Document as DocxDocument # python-docx pour DOCX
# import os
# import re # Nécessaire pour les expressions régulières futures
# from django.db import transaction
# from .utils import get_mongo_db

# # ==============================================================================
# # FONCTION D'EXTRACTION NETTE
# # ==============================================================================

# def extract_content_from_file(file_path, file_extension):
#     """
#     Extrait le contenu propre (texte brut) des fichiers PDF et DOCX pour la granulation.
#     """
#     if file_extension == 'pdf':
#         # Utilisation du mode 'text' pour obtenir le contenu le plus propre (sans le style HTML bruyant)
#         document = fitz.open(file_path)
#         raw_text = ""
#         for page_num in range(len(document)):
#             page = document.load_page(page_num)
#             raw_text += page.get_text("text")
#             raw_text += "\n\n--- PAGE BREAK ---\n\n" # Marqueur sémantique de page
#         return raw_text.strip()
    
#     elif file_extension in ['docx', 'doc']:
#         # Extraction du DOCX via python-docx
#         try:
#             document = DocxDocument(file_path)
#             # On prend le texte de chaque paragraphe
#             raw_text = "\n".join([paragraph.text for paragraph in document.paragraphs])
#             return raw_text.strip()
#         except Exception as e:
#             # Gérer les vieux formats .doc ou les fichiers corrompus
#             raise ValueError(f"Erreur lors de l'extraction DOCX: {e}")
            
#     else:
#         # Pour les fichiers texte simple
#         with open(file_path, 'r', encoding='utf-8') as f:
#             return f.read().strip()


# # ==============================================================================
# # PIPELINE DE TRAITEMENT (MISE À JOUR)
# # ==============================================================================

# def process_and_store_document(fichier_source_instance):
#     """
#     Pipeline de Traitement : Lit PDF/DOCX, convertit en texte propre,
#     stocke le texte dans MongoDB et met à jour MySQL.
#     """
#     file_path = fichier_source_instance.fichier_original.path
#     file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    
#     try:
#         # 1. Extraction NETTE (Texte pur, plus de bruit de style HTML)
#         raw_content = extract_content_from_file(file_path, file_extension)

#         # 2. Pré-transformation en HTML SÉMANTIQUE SIMPLE
#         # On remplace les doubles sauts de ligne par des balises <p> pour la lecture
#         semantic_html = f"<html><body><p>{raw_content.replace('\n\n', '</p><p>')}</p></body></html>"

#         # 3. Stockage dans MongoDB (Collection "fichiers_uploades")
#         mongo_db = get_mongo_db()
#         fichiers_collection = mongo_db['fichiers_uploades'] 
        
#         mongo_document = {
#             "fichier_source_id": str(fichier_source_instance.id),
#             "titre": fichier_source_instance.titre,
#             "type_original": file_extension.upper(),
#             "contenu_transforme": semantic_html, # Contenu propre pour la granulation
#             "date_traitement": fichier_source_instance.date_upload.isoformat()
#         }
        
#         result = fichiers_collection.insert_one(mongo_document)
#         mongo_id = str(result.inserted_id)
        
#         # 4. Mise à jour de l'instance MySQL
#         with transaction.atomic():
#             fichier_source_instance.mongo_transforme_id = mongo_id
#             fichier_source_instance.statut_traitement = 'TRAITE'
#             fichier_source_instance.type_mime = f'text/{file_extension}_clean'
#             fichier_source_instance.save()
        
#         return True, "Fichier traité et stocké dans MongoDB."
        
#     except Exception as e:
#         print(f"Erreur critique lors du traitement : {e}")
#         with transaction.atomic():
#             fichier_source_instance.statut_traitement = 'ERREUR'
#             fichier_source_instance.save()
#         return False, str(e)



# # xcsm/processing.py
# import fitz  # PyMuPDF pour PDF
# from docx import Document as DocxDocument # python-docx pour DOCX
# import os
# import re
# from django.db import transaction
# from .utils import get_mongo_db

# # ==============================================================================
# # 1. OUTILS D'EXTRACTION DE CONTENU PROPRE
# # ==============================================================================

# def extract_raw_text(file_path, file_extension):
#     """ Extrait le texte brut et le sépare par pages/paragraphes. """
#     raw_text = ""
#     if file_extension == 'pdf':
#         # Utiliser le mode 'text' pour obtenir du texte propre sans bruit CSS
#         document = fitz.open(file_path)
#         for page_num in range(len(document)):
#             page = document.load_page(page_num)
#             raw_text += page.get_text("text")
#             # Ajout d'un marqueur sémantique pour les sauts de page
#             raw_text += "\n\n--- PAGE BREAK ---\n\n"
    
#     elif file_extension == 'docx':
#         document = DocxDocument(file_path)
#         # On prend le texte de chaque paragraphe existant
#         raw_text = "\n".join([paragraph.text for paragraph in document.paragraphs])
        
#     return raw_text.strip()

# # ==============================================================================
# # 2. OUTIL DE CONVERSION SÉMANTIQUE (HEURISTIQUE : H1, H2, P)
# # ==============================================================================

# def segment_to_semantic_html(raw_content):
#     """
#     Convertit le texte brut en HTML sémantique (H1, H2, p) en utilisant 
#     des règles heuristiques (lignes vides, capitalisation, etc.).
#     """
    
#     # 1. Séparation par blocs de texte (séparés par deux retours chariot ou plus)
#     content_blocks = re.split(r'\n\s*\n', raw_content)
#     semantic_html = ""

#     for block in content_blocks:
#         block = block.strip()
#         if not block:
#             continue
            
#         # Détection du saut de page (pour la gestion future des granules)
#         if '--- PAGE BREAK ---' in block:
#             semantic_html += f"</div><div class='page_break'><hr/>" # Ferme le bloc et ajoute un séparateur
#             block = block.replace('--- PAGE BREAK ---', '').strip()
#             if not block:
#                 continue

#         # Tentative de détection de titre (Heuristique forte)
#         # Conditions : Ligne unique, courte (< 150), et sans ponctuation de fin
#         is_single_line = len(block.split('\n')) == 1
#         is_short = len(block) < 150
#         is_title_candidate = is_single_line and is_short and not re.search(r'[.!?]$', block)

#         if is_title_candidate:
#             # Heuristique pour H1 (Tout en majuscules)
#             if block.isupper() and len(block) < 80:
#                 semantic_html += f"<h1>{block}</h1>\n"
#             # Heuristique pour H2 (Titre normal)
#             else:
#                 semantic_html += f"<h2>{block}</h2>\n"
        
#         else:
#             # Traiter comme un paragraphe normal
#             # On réunit les retours chariot simples pour former un paragraphe complet
#             paragraph_text = ' '.join(block.split('\n')).strip()
#             if paragraph_text:
#                 semantic_html += f"<p>{paragraph_text}</p>\n"
            
#     return f"<html><body>{semantic_html}</body></html>"


# # ==============================================================================
# # 3. PIPELINE DE TRAITEMENT (Utilise le nouveau segmenter sémantique)
# # ==============================================================================

# def process_and_store_document(fichier_source_instance):
#     """
#     Pipeline de Traitement : Lit PDF/DOCX, extrait le texte, le segmente 
#     en HTML sémantique (H1, H2, p), puis le stocke dans MongoDB.
#     """
#     file_path = fichier_source_instance.fichier_original.path
#     file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    
#     try:
#         # 1. Extraction NETTE (Texte pur)
#         raw_content = extract_raw_text(file_path, file_extension)

#         # 2. Pré-transformation en HTML SÉMANTIQUE SIMPLE
#         semantic_html = segment_to_semantic_html(raw_content)

#         # 3. Stockage dans MongoDB
#         mongo_db = get_mongo_db()
#         fichiers_collection = mongo_db['fichiers_uploades'] 
        
#         mongo_document = {
#             "fichier_source_id": str(fichier_source_instance.id),
#             "titre": fichier_source_instance.titre,
#             "type_original": file_extension.upper(),
#             "contenu_transforme": semantic_html, 
#             "date_traitement": fichier_source_instance.date_upload.isoformat()
#         }
        
#         result = fichiers_collection.insert_one(mongo_document)
#         mongo_id = str(result.inserted_id)
        
#         # 4. Mise à jour de l'instance MySQL
#         with transaction.atomic():
#             fichier_source_instance.mongo_transforme_id = mongo_id
#             fichier_source_instance.statut_traitement = 'TRAITE'
#             fichier_source_instance.type_mime = f'text/html_semantic'
#             fichier_source_instance.save()
        
#         return True, "Fichier traité et stocké dans MongoDB."
        
#     except Exception as e:
#         print(f"Erreur critique lors du traitement : {e}")
#         with transaction.atomic():
#             fichier_source_instance.statut_traitement = 'ERREUR'
#             fichier_source_instance.save()
#         return False, str(e)
    
    
    
    
    
    



















# # xcsm/processing.py - V2.0 : Extraction Sémantique Propre (H1, H2, P)
# import fitz  # PyMuPDF pour PDF
# import os
# import re
# import io # Pour la manipulation de fichiers en mémoire
# import mammoth # Pour la conversion DOCX -> HTML Sémantique

# from django.db import transaction
# from .utils import get_mongo_db

# # ==============================================================================
# # 1. OUTILS D'EXTRACTION SPÉCIALISÉS (Mammoth pour DOCX, PyMuPDF pour PDF)
# # ==============================================================================

# def convert_docx_to_semantic_html(file_path):
#     """ 
#     Utilise Mammoth pour convertir un DOCX en HTML sémantique propre (H1, H2, P). 
#     Mammoth est excellent car il utilise les styles Word (Titre 1, Titre 2)
#     pour générer directement les balises sémantiques.
#     """
#     # Style map pour s'assurer que Word 'Heading 1' devient <h1>, etc.
#     STYLE_MAP = """
#     heading1 => h1:fresh
#     heading2 => h2:fresh
#     heading3 => h3:fresh
#     p => p:fresh
#     """
    
#     # On lit le fichier en bytes pour le passer à mammoth
#     with open(file_path, 'rb') as docx_file:
#         result = mammoth.convert_to_html(docx_file, style_map=STYLE_MAP)
#         html = result.value
        
#     return f"<html><body>{html}</body></html>"




# # Remplacement de la fonction convert_pdf_to_semantic_html dans xcsm/processing.py
# def convert_pdf_to_semantic_html(file_path):
#     """
#     Utilise PyMuPDF pour extraire du texte pur et applique une heuristique sémantique.
#     Mise à jour pour:
#     1. Forcer chaque ligne d'un bloc en <p>.
#     2. Améliorer la détection H2 (Ex: "I. Cloner le Dépôt...").
#     """
#     document = fitz.open(file_path)
#     raw_text = ""
#     for page_num in range(len(document)):
#         page = document.load_page(page_num)
#         # Extraction du texte pur (mode 'text') pour éliminer TOUT le bruit CSS
#         raw_text += page.get_text("text") 
#         raw_text += "\n\n--- PAGE BREAK ---\n\n"
        
#     # Appliquer l'heuristique sémantique sur le texte brut pour trouver H1/H2
#     # Séparation par blocs de texte (séparés par deux retours chariot ou plus)
#     content_blocks = re.split(r'\n\s*\n', raw_text)
#     semantic_html = ""

#     for block in content_blocks:
#         block = block.strip()
#         if not block or '--- PAGE BREAK ---' in block:
#             continue
            
#         # Détection de titre (heuristique améliorée)
#         # Condition : Ligne unique, courte (< 150), ET commence par un chiffre romain (I., II., etc.) ou est tout en majuscules
        
#         is_single_line = len(block.split('\n')) == 1
#         is_short = len(block) < 150
        
#         # Heuristique Titre H2 (Ex: "I. Cloner le Dépôt..." ou "II. Cycle de Contribution...")
#         is_h2_candidate = is_single_line and is_short and re.match(r'^[IVX]+\.\s+', block)
        
#         # Heuristique Titre H1 (Tout en majuscules, très court)
#         is_h1_candidate = is_single_line and block.isupper() and len(block) < 80
        
#         if is_h1_candidate:
#             semantic_html += f"<h1>{block}</h1>\n"
            
#         elif is_h2_candidate:
#             # Nettoyage des caractères spéciaux et des espaces multiples
#             clean_block = re.sub(r'[\u00A0\t ]+', ' ', block).strip()
#             semantic_html += f"<h2>{clean_block}</h2>\n"
        
#         else:
#             # === NOUVEAU : Traitement ligne par ligne pour la granulation ===
#             # On splitte le bloc par les retours à la ligne simples
#             lines = [line.strip() for line in block.split('\n')]
            
#             for line in lines:
#                 if line:
#                     # Nettoyage des caractères spéciaux et des espaces multiples
#                     clean_line = re.sub(r'[\u00A0\t ]+', ' ', line).strip()
#                     # Chaque ligne propre devient un paragraphe indépendant
#                     semantic_html += f"<p>{clean_line}</p>\n"
            
#     return f"<html><body>{semantic_html}</body></html>"



# # ==============================================================================
# # 2. PIPELINE DE TRAITEMENT (ORCHESTRATEUR)
# # ==============================================================================

# def process_and_store_document(fichier_source_instance):
#     """
#     Orchestre le processus de conversion, du fichier à MongoDB.
#     """
#     file_path = fichier_source_instance.fichier_original.path
#     file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    
#     try:
#         # 1. SÉLECTION DU MOTEUR SPÉCIALISÉ
#         if file_extension == 'docx':
#             semantic_html = convert_docx_to_semantic_html(file_path)
#         elif file_extension == 'pdf':
#             semantic_html = convert_pdf_to_semantic_html(file_path)
#         else:
#             # Fallback simple pour TXT
#             with open(file_path, 'r', encoding='utf-8') as f:
#                 raw_text = f.read()
#             semantic_html = f"<html><body><p>{raw_text.replace('\n\n', '</p><p>')}</p></body></html>"
        
#         if not semantic_html or len(semantic_html) < 50:
#             raise ValueError(f"Conversion échouée: Contenu HTML vide ou trop court après traitement du {file_extension.upper()}.")

#         # 2. Stockage dans MongoDB
#         mongo_db = get_mongo_db()
#         fichiers_collection = mongo_db['fichiers_uploades'] 
        
#         mongo_document = {
#             "fichier_source_id": str(fichier_source_instance.id),
#             "titre": fichier_source_instance.titre,
#             "type_original": file_extension.upper(),
#             "contenu_transforme": semantic_html, # Contenu SÉMANTIQUE PROPRE et structuré
#             "date_traitement": fichier_source_instance.date_upload.isoformat()
#         }
        
#         result = fichiers_collection.insert_one(mongo_document)
#         mongo_id = str(result.inserted_id)
        
#         # 3. Mise à jour de l'instance MySQL
#         with transaction.atomic():
#             fichier_source_instance.mongo_transforme_id = mongo_id
#             fichier_source_instance.statut_traitement = 'TRAITE'
#             fichier_source_instance.type_mime = f'text/html_semantic'
#             fichier_source_instance.save()
        
#         return True, "Fichier traité et stocké dans MongoDB."
        
#     except Exception as e:
#         print(f"Erreur critique lors du traitement : {e}")
#         with transaction.atomic():
#             fichier_source_instance.statut_traitement = 'ERREUR'
#             fichier_source_instance.save()
#         return False, str(e)










# xcsm/processing.py
import fitz  # PyMuPDF pour PDF
import os
import re
import io
import mammoth # Pour la conversion DOCX
from bs4 import BeautifulSoup # Pour le nettoyage final
from django.db import transaction
from .utils import get_mongo_db

# ==============================================================================
# 1. OUTIL DE POST-TRAITEMENT (Cœur de la Granulation)
# ==============================================================================

def post_process_semantic_html(raw_html: str) -> str:
    """
    Fonction CRITIQUE : Prend du HTML brut et force le découpage ligne par ligne.
    Transforme les blocs <p> multi-lignes en plusieurs <p> unitaires.
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    new_body = ""
    
    # On parcourt chaque élément de premier niveau (H1, P, UL, etc.)
    for element in soup.body.contents:
        if element.name is None: # Ignore les sauts de ligne entre les balises
            continue
            
        tag_name = element.name
        text = element.get_text().strip()
        
        if not text:
            continue
            
        # A. LES TITRES : On les garde intacts (Unités sémantiques fortes)
        if tag_name in ['h1', 'h2', 'h3', 'h4']:
            new_body += f"<{tag_name}>{text}</{tag_name}>\n"
        
        # B. LES PARAGRAPHES & LISTES : On découpe chaque ligne !
        elif tag_name in ['p', 'li', 'ul', 'ol', 'div']:
            # On sépare par les retours à la ligne présents dans le texte source
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                # Nettoyage des caractères invisibles (espaces insécables, tabulations)
                clean_line = re.sub(r'[\u00A0\t\r]+', ' ', line).strip()
                
                # Heuristique : Si la ligne commence par un tiret ou un chiffre, c'est une liste
                if re.match(r'^[-•*]\s+', clean_line) or re.match(r'^\d+\.\s+', clean_line):
                    # On peut choisir de garder <p> ou mettre <li>, restons sur <p> pour la simplicité
                    new_body += f"<p>{clean_line}</p>\n"
                elif clean_line:
                    new_body += f"<p>{clean_line}</p>\n"
        
        # C. AUTRES (Images, Tableaux...) : On garde tel quel
        else:
            new_body += str(element) + "\n"

    return f"<html><body>\n{new_body}</body></html>"

# ==============================================================================
# 2. CONVERTISSEURS SPÉCIFIQUES
# ==============================================================================

def convert_docx_to_semantic_html(file_path):
    """ Utilise Mammoth pour DOCX + Post-traitement granulaire """
    # Mapping strict pour récupérer les vrais titres Word
    style_map = """
    p[style-name='Title'] => h1:fresh
    p[style-name='Heading 1'] => h1:fresh
    p[style-name='Heading 2'] => h2:fresh
    p[style-name='Heading 3'] => h3:fresh
    """
    
    with open(file_path, 'rb') as docx_file:
        # Mammoth convertit le DOCX en HTML brut
        result = mammoth.convert_to_html(docx_file, style_map=style_map)
        raw_html = f"<html><body>{result.value}</body></html>"
        
    # On passe le résultat à notre découpeur ligne par ligne
    return post_process_semantic_html(raw_html)


def convert_pdf_to_semantic_html(file_path):
    """ Utilise PyMuPDF + Heuristique Titres + Post-traitement granulaire """
    document = fitz.open(file_path)
    raw_text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        raw_text += page.get_text("text") 
        raw_text += "\n" # Séparateur simple
        
    content_blocks = re.split(r'\n\s*\n', raw_text)
    semantic_parts = ""
    
    for block in content_blocks:
        block = block.strip()
        if not block or '--- PAGE BREAK ---' in block: continue
            
        # Détection H1/H2 (Ligne unique, courte, majuscule ou numérotée)
        is_single = len(block.split('\n')) == 1
        is_short = len(block) < 150
        
        if is_single and is_short and (block.isupper() or re.match(r'^[IVX]+\.', block)):
             # C'est un titre -> On l'enveloppe direct
             tag = 'h1' if block.isupper() else 'h2'
             semantic_parts += f"<{tag}>{block}</{tag}>\n"
        else:
             # C'est du texte -> On le met dans un <p> temporaire
             # Le post-processeur se chargera de le redécouper ligne par ligne
             semantic_parts += f"<p>{block}</p>\n"
                
    return post_process_semantic_html(f"<html><body>{semantic_parts}</body></html>")

# ==============================================================================
# 3. ORCHESTRATEUR (INCHANGÉ)
# ==============================================================================

def process_and_store_document(fichier_source_instance):
    file_path = fichier_source_instance.fichier_original.path
    file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    
    try:
        if file_extension == 'docx':
            semantic_html = convert_docx_to_semantic_html(file_path)
        elif file_extension == 'pdf':
            semantic_html = convert_pdf_to_semantic_html(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Pour le TXT, on traite chaque ligne comme un paragraphe
                raw = f.read()
                semantic_html = f"<html><body><p>{raw}</p></body></html>"
                semantic_html = post_process_semantic_html(semantic_html)
        
        if not semantic_html or len(semantic_html) < 50:
            raise ValueError(f"Contenu vide ou trop court.")

        mongo_db = get_mongo_db()
        mongo_document = {
            "fichier_source_id": str(fichier_source_instance.id),
            "titre": fichier_source_instance.titre,
            "type_original": file_extension.upper(),
            "contenu_transforme": semantic_html,
            "date_traitement": fichier_source_instance.date_upload.isoformat()
        }
        
        result = mongo_db['fichiers_uploades'].insert_one(mongo_document)
        
        with transaction.atomic():
            fichier_source_instance.mongo_transforme_id = str(result.inserted_id)
            fichier_source_instance.statut_traitement = 'TRAITE'
            fichier_source_instance.save()
        
        return True, "Fichier traité et stocké."
        
    except Exception as e:
        print(f"Erreur : {e}")
        with transaction.atomic():
            fichier_source_instance.statut_traitement = 'ERREUR'
            fichier_source_instance.save()
        return False, str(e)

