# import fitz                   # Pour PyMuPDF
# import os
# import re
# import io
# import mammoth                # Pour la conversion DOCX
# from bs4 import BeautifulSoup # Pour le nettoyage final
# from django.db import transaction
# from .utils import get_mongo_db
# # IMPORTS NÉCESSAIRES POUR LE DÉCOUPAGE (MySQL Models)
# from .models import Cours, Partie, Chapitre, Section, SousSection, Granule



# # ==============================================================================
# # 1. OUTIL DE POST-TRAITEMENT (Cœur de la Granulation)
# # ==============================================================================

# def post_process_semantic_html(raw_html: str) -> str:
#     """
#     Fonction CRITIQUE : Prend du HTML brut et force le découpage ligne par ligne.
#     Transforme les blocs <p> multi-lignes en plusieurs <p> unitaires.
#     """
#     soup = BeautifulSoup(raw_html, 'html.parser')
#     new_body = ""
    
#     # On parcourt chaque élément de premier niveau (H1, P, UL, etc.)
#     for element in soup.body.contents:
#         if element.name is None: # Ignore les sauts de ligne entre les balises
#             continue
            
#         tag_name = element.name
#         text = element.get_text().strip()
        
#         if not text:
#             continue
            
#         # A. LES TITRES : On les garde intacts (Unités sémantiques fortes)
#         if tag_name in ['h1', 'h2', 'h3', 'h4']:
#             new_body += f"<{tag_name}>{text}</{tag_name}>\n"
        
#         # B. LES PARAGRAPHES & LISTES : On découpe chaque ligne !
#         elif tag_name in ['p', 'li', 'ul', 'ol', 'div']:
#             # On sépare par les retours à la ligne présents dans le texte source
#             lines = [line.strip() for line in text.split('\n') if line.strip()]
            
#             for line in lines:
#                 # Nettoyage des caractères invisibles (espaces insécables, tabulations)
#                 clean_line = re.sub(r'[\u00A0\t\r]+', ' ', line).strip()
                
#                 # Heuristique : Si la ligne commence par un tiret ou un chiffre, c'est une liste
#                 if re.match(r'^[-•*]\s+', clean_line) or re.match(r'^\d+\.\s+', clean_line):
#                     # On peut choisir de garder <p> ou mettre <li>, restons sur <p> pour la simplicité
#                     new_body += f"<p>{clean_line}</p>\n"
#                 elif clean_line:
#                     new_body += f"<p>{clean_line}</p>\n"
        
#         # C. AUTRES (Images, Tableaux...) : On garde tel quel
#         else:
#             new_body += str(element) + "\n"

#     return f"<html><body>\n{new_body}</body></html>"

# # ==============================================================================
# # 2. CONVERTISSEURS SPÉCIFIQUES
# # ==============================================================================

# def convert_docx_to_semantic_html(file_path):
#     """ Utilise Mammoth pour DOCX + Post-traitement granulaire """
#     # Mapping strict pour récupérer les vrais titres Word
#     style_map = """
#     p[style-name='Title'] => h1:fresh
#     p[style-name='Heading 1'] => h1:fresh
#     p[style-name='Heading 2'] => h2:fresh
#     p[style-name='Heading 3'] => h3:fresh
#     """
    
#     with open(file_path, 'rb') as docx_file:
#         # Mammoth convertit le DOCX en HTML brut
#         result = mammoth.convert_to_html(docx_file, style_map=style_map)
#         raw_html = f"<html><body>{result.value}</body></html>"
        
#     # On passe le résultat à notre découpeur ligne par ligne
#     return post_process_semantic_html(raw_html)


# def convert_pdf_to_semantic_html(file_path):
#     """ Utilise PyMuPDF + Heuristique Titres + Post-traitement granulaire """
#     document = fitz.open(file_path)
#     raw_text = ""
#     for page_num in range(len(document)):
#         page = document.load_page(page_num)
#         raw_text += page.get_text("text") 
#         raw_text += "\n" # Séparateur simple
        
#     content_blocks = re.split(r'\n\s*\n', raw_text)
#     semantic_parts = ""
    
#     for block in content_blocks:
#         block = block.strip()
#         if not block or '--- PAGE BREAK ---' in block: continue
            
#         # Détection H1/H2 (Ligne unique, courte, majuscule ou numérotée)
#         is_single = len(block.split('\n')) == 1
#         is_short = len(block) < 150
        
#         if is_single and is_short and (block.isupper() or re.match(r'^[IVX]+\.', block)):
#              # C'est un titre -> On l'enveloppe direct
#              tag = 'h1' if block.isupper() else 'h2'
#              semantic_parts += f"<{tag}>{block}</{tag}>\n"
#         else:
#              # C'est du texte -> On le met dans un <p> temporaire
#              # Le post-processeur se chargera de le redécouper ligne par ligne
#              semantic_parts += f"<p>{block}</p>\n"
                
#     return post_process_semantic_html(f"<html><body>{semantic_parts}</body></html>")


# # ==============================================================================
# # 3. MOTEUR DE DÉCOUPAGE (GRANULATION)
# # ==============================================================================

# def split_and_create_granules(fichier_source, html_content):
#     """
#     Analyse le HTML sémantique et peuple la base de données MySQL et MongoDB.
#     Crée la hiérarchie : Cours -> Partie -> Chapitre -> Section -> Granule
#     """
#     mongo_db = get_mongo_db()
#     granules_collection = mongo_db['granules']
    
#     soup = BeautifulSoup(html_content, 'html.parser')
    
#     # 1. Création du Conteneur Principal (Le Cours Brouillon)
#     # On vérifie si un cours existe déjà pour ce fichier, sinon on crée
#     cours, created = Cours.objects.get_or_create(
#         code=f"AUTO-{fichier_source.id.hex[:8].upper()}", # Code temporaire unique
#         defaults={
#             'enseignant': fichier_source.enseignant,
#             'titre': f"Cours issu de : {fichier_source.titre}",
#             'description': "Généré automatiquement par XCSM",
#             'matiere': "Non définie",
#             'niveau': "Non défini",
#             'est_publie': False
#         }
#     )
    
#     # Création d'une Partie par défaut (Racine)
#     partie_actuelle = Partie.objects.create(
#         cours=cours,
#         titre="Partie Principale",
#         numero=1
#     )
    
#     # Pointeurs de contexte (pour savoir où ranger les granules)
#     chapitre_actuel = None
#     section_actuelle = None
#     sous_section_actuelle = None
    
#     # Compteurs pour l'ordre
#     ordres = {'chapitre': 1, 'section': 1, 'sous_section': 1, 'granule': 1}

#     # 2. Parcours séquentiel du HTML
#     for element in soup.body.contents:
#         if element.name is None: continue
        
#         tag = element.name
#         text = element.get_text().strip()
#         if not text: continue

#         # --- NIVEAU 1 : CHAPITRE (H1) ---
#         if tag == 'h1':
#             chapitre_actuel = Chapitre.objects.create(
#                 partie=partie_actuelle,
#                 titre=text[:199], # Limite charfield
#                 numero=ordres['chapitre']
#             )
#             ordres['chapitre'] += 1
#             # Reset des niveaux inférieurs
#             section_actuelle = None 
#             sous_section_actuelle = None
#             ordres['section'] = 1

#         # --- NIVEAU 2 : SECTION (H2) ---
#         elif tag == 'h2':
#             # Si pas de chapitre, on en crée un par défaut
#             if not chapitre_actuel:
#                 chapitre_actuel = Chapitre.objects.create(partie=partie_actuelle, titre="Introduction", numero=ordres['chapitre'])
#                 ordres['chapitre'] += 1
            
#             section_actuelle = Section.objects.create(
#                 chapitre=chapitre_actuel,
#                 titre=text[:199],
#                 numero=ordres['section']
#             )
#             ordres['section'] += 1
#             # Reset niveau inférieur
#             sous_section_actuelle = None
#             ordres['sous_section'] = 1

#         # --- NIVEAU 3 : GRANULE (P, LI, etc.) ---
#         elif tag in ['p', 'li', 'ul', 'ol', 'div', 'h3']: 
#             # Note: On traite H3 comme un granule de titre pour simplifier, ou on pourrait créer SousSection
            
#             # Gestion de la hiérarchie minimale pour attacher le granule
#             if not section_actuelle:
#                 if not chapitre_actuel:
#                     chapitre_actuel = Chapitre.objects.create(partie=partie_actuelle, titre="Introduction Générale", numero=ordres['chapitre'])
#                 section_actuelle = Section.objects.create(chapitre=chapitre_actuel, titre="Section Générale", numero=ordres['section'])
            
#             # Si pas de sous-section, on en crée une "contenu" par défaut ou on attache à une sous-section générique
#             if not sous_section_actuelle:
#                 sous_section_actuelle = SousSection.objects.create(
#                     section=section_actuelle, 
#                     titre="Contenu", 
#                     numero=ordres['sous_section']
#                 )
#                 ordres['sous_section'] += 1

#             # A. Stockage Contenu Riche dans MongoDB
#             granule_mongo = {
#                 "html_content": str(element), # On garde le HTML (<p>...</p>)
#                 "texte_brut": text,
#                 "fichier_source_id": str(fichier_source.id)
#             }
#             res_mongo = granules_collection.insert_one(granule_mongo)
            
#             # B. Création Métadonnées dans MySQL
#             Granule.objects.create(
#                 sous_section=sous_section_actuelle,
#                 fichier_source=fichier_source,
#                 titre=text[:50] + "..." if len(text) > 50 else text, # Aperçu du titre
#                 type_contenu="TEXTE",
#                 mongo_contenu_id=str(res_mongo.inserted_id),
#                 ordre=ordres['granule']
#             )
#             ordres['granule'] += 1

#     return cours

# # ==============================================================================
# # 3. ORCHESTRATEUR (INCHANGÉ)
# # ==============================================================================

# def process_and_store_document(fichier_source_instance):
#     file_path = fichier_source_instance.fichier_original.path
#     file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    
#     try:
#         # 1. Extraction & Nettoyage
#         if file_extension == 'docx':
#             semantic_html = convert_docx_to_semantic_html(file_path)
#         elif file_extension == 'pdf':
#             semantic_html = convert_pdf_to_semantic_html(file_path)
#         else:
#             with open(file_path, 'r', encoding='utf-8') as f:
#                 semantic_html = post_process_semantic_html(f"<html><body><p>{f.read()}</p></body></html>")
        
#         if not semantic_html or len(semantic_html) < 50:
#             raise ValueError("Contenu vide ou trop court.")

#         # 2. Stockage HTML Global (MongoDB)
#         mongo_db = get_mongo_db()
#         res = mongo_db['fichiers_uploades'].insert_one({
#             "fichier_source_id": str(fichier_source_instance.id),
#             "titre": fichier_source_instance.titre,
#             "type_original": file_extension.upper(),
#             "contenu_transforme": semantic_html,
#             "date_traitement": fichier_source_instance.date_upload.isoformat()
#         })
        
#         # 3. DÉCOUPAGE INTELLIGENT (Nouvelle étape)
#         # On passe le HTML propre au moteur de découpage
#         cours_genere = split_and_create_granules(fichier_source_instance, semantic_html)
        
#         # 4. Finalisation MySQL
#         with transaction.atomic():
#             fichier_source_instance.mongo_transforme_id = str(res.inserted_id)
#             fichier_source_instance.statut_traitement = 'TRAITE'
#             fichier_source_instance.type_mime = f'text/html_semantic'
#             fichier_source_instance.save()
        
#         return True, f"Traité avec succès. Cours généré : {cours_genere.titre}"
        
#     except Exception as e:
#         print(f"Erreur : {e}")
#         with transaction.atomic():
#             fichier_source_instance.statut_traitement = 'ERREUR'
#             fichier_source_instance.save()
#         return False, str(e)








# # xcsm/processing.py - V4.0 : VERSION CORRIGÉE (Suppression champs invalides)
# import fitz  # PyMuPDF
# import os
# import re
# import mammoth
# from bs4 import BeautifulSoup, NavigableString
# from django.db import transaction
# from .utils import get_mongo_db
# # Imports des modèles MySQL pour la hiérarchie
# from .models import Cours, Partie, Chapitre, Section, SousSection, Granule

# # ==============================================================================
# # 1. OUTILS DE NETTOYAGE ET CONVERSION
# # ==============================================================================

# def post_process_semantic_html(raw_html: str) -> str:
#     """ Nettoie le HTML et force le découpage ligne par ligne. """
#     soup = BeautifulSoup(raw_html, 'html.parser')
#     new_body = ""
    
#     content_source = soup.body.contents if soup.body else soup.contents
    
#     for element in content_source:
#         if element.name is None:
#             text = str(element).strip()
#             if text: new_body += f"<p>{text}</p>\n"
#             continue
            
#         tag = element.name
#         text = element.get_text().strip()
#         if not text: continue
        
#         if tag in ['h1', 'h2', 'h3', 'h4']:
#             new_body += f"<{tag}>{text}</{tag}>\n"
#         elif tag in ['p', 'li', 'ul', 'ol', 'div']:
#             lines = [line.strip() for line in text.split('\n') if line.strip()]
#             for line in lines:
#                 clean = re.sub(r'[\u00A0\t ]+', ' ', line).strip()
#                 if clean: new_body += f"<p>{clean}</p>\n"
#         else:
#             new_body += str(element) + "\n"

#     return f"<html><body>\n{new_body}</body></html>"

# def convert_docx_to_semantic_html(file_path):
#     style_map = """
#     p[style-name='Title'] => h1:fresh
#     p[style-name='Heading 1'] => h1:fresh
#     p[style-name='Heading 2'] => h2:fresh
#     p[style-name='Heading 3'] => h3:fresh
#     p => p:fresh
#     """
#     with open(file_path, 'rb') as f:
#         res = mammoth.convert_to_html(f, style_map=style_map)
#     return post_process_semantic_html(f"<html><body>{res.value}</body></html>")

# def convert_pdf_to_semantic_html(file_path):
#     doc = fitz.open(file_path)
#     text = ""
#     for p in doc: text += p.get_text("text") + "\n\n--- PAGE BREAK ---\n\n"
    
#     parts = ""
#     for block in re.split(r'\n\s*\n', text):
#         block = block.strip()
#         if not block or '--- PAGE' in block: continue
        
#         is_single = len(block.split('\n')) == 1 and len(block) < 150
#         is_h1 = is_single and block.isupper()
#         is_h2 = is_single and (re.match(r'^[IVX0-9]+\.', block) or block.endswith(':'))
        
#         if is_h1: parts += f"<h1>{block}</h1>\n"
#         elif is_h2: parts += f"<h2>{block}</h2>\n"
#         else: parts += f"<p>{block}</p>\n"
            
#     return post_process_semantic_html(f"<html><body>{parts}</body></html>")

# # ==============================================================================
# # 2. MOTEUR DE DÉCOUPAGE (CORRECTION DU BUG 'Matiere/Niveau')
# # ==============================================================================

# def split_and_create_granules(fichier_source, html_content):
#     mongo_db = get_mongo_db()
#     granules_col = mongo_db['granules']
#     soup = BeautifulSoup(html_content, 'html.parser')
    
#     # A. NETTOYAGE
#     Granule.objects.filter(fichier_source=fichier_source).delete()
    
#     # B. CRÉATION DU COURS (CORRIGÉ)
#     # Suppression de 'matiere' et 'niveau' qui n'existent pas dans models.py
#     code_unique = f"C-{fichier_source.id.hex[:6].upper()}"
#     cours, _ = Cours.objects.get_or_create(
#         code=code_unique,
#         defaults={
#             'enseignant': fichier_source.enseignant,
#             'titre': fichier_source.titre,
#             'description': "Généré automatiquement par XCSM",
#             'est_publie': False
#             # 'matiere' et 'niveau' RETIRÉS CAR ABSENTS DU MODÈLE
#         }
#     )
#     Partie.objects.filter(cours=cours).delete()
    
#     # C. INITIALISATION
#     partie = Partie.objects.create(cours=cours, titre="Contenu Principal", numero=1)
#     chapitre = Chapitre.objects.create(partie=partie, titre="Introduction", numero=1)
#     section = Section.objects.create(chapitre=chapitre, titre="Généralités", numero=1)
#     sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)
    
#     cpt = {'chap': 1, 'sec': 1, 'granule': 1}

#     # D. BOUCLE
#     root = soup.body if soup.body else soup
#     for el in root.contents:
#         if el.name is None: continue
#         tag = el.name
#         text = el.get_text().strip()
#         if not text: continue

#         if tag == 'h1':
#             cpt['chap'] += 1
#             chapitre = Chapitre.objects.create(partie=partie, titre=text[:190], numero=cpt['chap'])
#             section = Section.objects.create(chapitre=chapitre, titre="Début", numero=1)
#             sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)
#             cpt['sec'] = 1

#         elif tag == 'h2':
#             cpt['sec'] += 1
#             section = Section.objects.create(chapitre=chapitre, titre=text[:190], numero=cpt['sec'])
#             sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)

#         elif tag in ['p', 'li', 'div', 'h3', 'h4']:
#             doc_mongo = {'html': str(el), 'text': text, 'fichier_id': str(fichier_source.id), 'type': 'TEXTE'}
#             res = granules_col.insert_one(doc_mongo)
            
#             Granule.objects.create(
#                 sous_section=sous_section,
#                 fichier_source=fichier_source,
#                 titre=text[:45] + "..." if len(text)>45 else text,
#                 type_contenu="TEXTE",
#                 mongo_contenu_id=str(res.inserted_id),
#                 ordre=cpt['granule']
#             )
#             cpt['granule'] += 1
            
#     return cours

# # ==============================================================================
# # 3. ORCHESTRATEUR
# # ==============================================================================

# def process_and_store_document(fichier_source_instance):
#     try:
#         path = fichier_source_instance.fichier_original.path
#         ext = os.path.splitext(path)[1].lower().strip('.')
        
#         if ext == 'docx': html = convert_docx_to_semantic_html(path)
#         elif ext == 'pdf': html = convert_pdf_to_semantic_html(path)
#         else: html = post_process_semantic_html(f"<html><body><p>{open(path, encoding='utf-8').read()}</p></body></html>")
        
#         if len(html) < 20: raise ValueError("HTML vide.")

#         mdb = get_mongo_db()
#         mdb['fichiers_uploades'].insert_one({
#            "fichier_source_id": str(fichier_source_instance.id),
#             "titre": fichier_source_instance.titre,
#             "type_original": file_extension.upper(),
#             "contenu_transforme": semantic_html,
#             "date_traitement": fichier_source_instance.date_upload.isoformat()
#         })
        
#         cours = split_and_create_granules(fichier_source_instance, html)
        
#         with transaction.atomic():
#             fichier_source_instance.statut_traitement = 'TRAITE'
#             fichier_source_instance.save()
            
#         return True, f"Cours généré : {cours.titre} ({cours.code})"
        
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return False, str(e)





# xcsm/processing.py - Version JSON Structuré (Refonte Complète)
import fitz  # PyMuPDF
import os
import re
import mammoth
from bs4 import BeautifulSoup
from django.db import transaction
from .utils import get_mongo_db
from .models import Cours, Partie, Chapitre, Section, SousSection, Granule
from datetime import datetime

# ==============================================================================
# 1. CONVERSION VERS JSON STRUCTURÉ (Remplacement du HTML)
# ==============================================================================

def extract_structure_from_docx(file_path):
    """
    Convertit un DOCX en JSON structuré avec hiérarchie sémantique.
    Retourne: {"metadata": {...}, "sections": [...]}
    """
    style_map = """
    p[style-name='Title'] => h1:fresh
    p[style-name='Heading 1'] => h1:fresh
    p[style-name='Heading 2'] => h2:fresh
    p[style-name='Heading 3'] => h3:fresh
    """
    
    with open(file_path, 'rb') as f:
        result = mammoth.convert_to_html(f, style_map=style_map)
        html = f"<html><body>{result.value}</body></html>"
    
    return parse_html_to_json_structure(html)


def extract_structure_from_pdf(file_path):
    """
    Convertit un PDF en JSON structuré avec détection de hiérarchie.
    """
    doc = fitz.open(file_path)
    raw_text = ""
    
    for page in doc:
        raw_text += page.get_text("text") + "\n\n--- PAGE BREAK ---\n\n"
    
    # Construction du HTML intermédiaire pour réutiliser le parser
    html_parts = ""
    for block in re.split(r'\n\s*\n', raw_text):
        block = block.strip()
        if not block or '--- PAGE' in block:
            continue
        
        is_single_line = len(block.split('\n')) == 1
        is_short = len(block) < 150
        
        # Détection des titres
        if is_single_line and is_short:
            if block.isupper():
                html_parts += f"<h1>{block}</h1>\n"
            elif re.match(r'^[IVX0-9]+\.', block) or block.endswith(':'):
                html_parts += f"<h2>{block}</h2>\n"
            else:
                html_parts += f"<p>{block}</p>\n"
        else:
            html_parts += f"<p>{block}</p>\n"
    
    return parse_html_to_json_structure(f"<html><body>{html_parts}</body></html>")


def parse_html_to_json_structure(html_content):
    """
    CŒUR DE LA TRANSFORMATION : Convertit le HTML en structure JSON hiérarchique.
    Format de sortie:
    {
        "metadata": {"source_type": "pdf/docx", "extraction_date": "..."},
        "sections": [
            {
                "type": "h1/h2/p",
                "level": 1/2/3,
                "content": "texte brut",
                "html": "<h1>texte</h1>",  # Conservé pour compatibilité
                "children": [...]  # Granules enfants si applicable
            }
        ]
    }
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    root = soup.body if soup.body else soup
    
    structure = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "version": "2.0-JSON"
        },
        "sections": []
    }
    
    current_h1 = None
    current_h2 = None
    
    for element in root.contents:
        if element.name is None:
            continue
        
        tag = element.name
        text = element.get_text().strip()
        
        if not text:
            continue
        
        # Construction du nœud JSON
        node = {
            "type": tag,
            "level": get_semantic_level(tag),
            "content": text,
            "html": str(element),  # Conservé pour rétro-compatibilité
            "children": []
        }
        
        # Gestion de la hiérarchie
        if tag == 'h1':
            structure["sections"].append(node)
            current_h1 = node
            current_h2 = None
        
        elif tag == 'h2':
            if current_h1:
                current_h1["children"].append(node)
            else:
                structure["sections"].append(node)
            current_h2 = node
        
        elif tag in ['h3', 'p', 'li', 'div']:
            # Découpage ligne par ligne pour les paragraphes
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                clean_line = re.sub(r'[\u00A0\t\r]+', ' ', line).strip()
                if not clean_line:
                    continue
                
                granule_node = {
                    "type": "granule",
                    "level": 4,
                    "content": clean_line,
                    "html": f"<p>{clean_line}</p>"
                }
                
                # Attachement au bon parent
                if current_h2:
                    current_h2["children"].append(granule_node)
                elif current_h1:
                    current_h1["children"].append(granule_node)
                else:
                    structure["sections"].append(granule_node)
    
    return structure


def get_semantic_level(tag):
    """Retourne le niveau sémantique d'une balise."""
    levels = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'p': 4, 'li': 4, 'div': 4}
    return levels.get(tag, 5)


# ==============================================================================
# 2. DÉCOUPAGE ET STOCKAGE (Version JSON)
# ==============================================================================

def split_and_create_granules(fichier_source, json_structure):
    """
    Analyse la structure JSON et crée la hiérarchie MySQL + stockage MongoDB.
    """
    mongo_db = get_mongo_db()
    granules_col = mongo_db['granules']
    
    # A. NETTOYAGE des anciens granules
    Granule.objects.filter(fichier_source=fichier_source).delete()
    
    # B. CRÉATION DU COURS
    code_unique = f"C-{fichier_source.id.hex[:6].upper()}"
    cours, _ = Cours.objects.get_or_create(
        code=code_unique,
        defaults={
            'enseignant': fichier_source.enseignant,
            'titre': fichier_source.titre,
            'description': "Généré automatiquement - Version JSON",
            'est_publie': False
        }
    )
    
    # Nettoyage des anciennes parties
    Partie.objects.filter(cours=cours).delete()
    
    # C. INITIALISATION DE LA HIÉRARCHIE
    partie = Partie.objects.create(cours=cours, titre="Contenu Principal", numero=1)
    chapitre = Chapitre.objects.create(partie=partie, titre="Introduction", numero=1)
    section = Section.objects.create(chapitre=chapitre, titre="Généralités", numero=1)
    sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)
    
    counters = {'chapitre': 1, 'section': 1, 'granule': 1}
    
    # D. PARCOURS DE LA STRUCTURE JSON
    for node in json_structure.get("sections", []):
        process_json_node(
            node, fichier_source, granules_col,
            partie, chapitre, section, sous_section, counters
        )
    
    return cours


def process_json_node(node, fichier_source, granules_col, 
                     partie, chapitre, section, sous_section, counters):
    """
    Traite récursivement un nœud JSON et crée les entités MySQL/MongoDB.
    """
    node_type = node.get("type")
    content = node.get("content", "")
    children = node.get("children", [])
    
    # NIVEAU 1: CHAPITRE (H1)
    if node_type == 'h1':
        counters['chapitre'] += 1
        chapitre = Chapitre.objects.create(
            partie=partie,
            titre=content[:190],
            numero=counters['chapitre']
        )
        section = Section.objects.create(
            chapitre=chapitre, 
            titre="Début", 
            numero=1
        )
        sous_section = SousSection.objects.create(
            section=section, 
            titre="Contenu", 
            numero=1
        )
        counters['section'] = 1
        
        # Traitement des enfants
        for child in children:
            process_json_node(
                child, fichier_source, granules_col,
                partie, chapitre, section, sous_section, counters
            )
    
    # NIVEAU 2: SECTION (H2)
    elif node_type == 'h2':
        counters['section'] += 1
        section = Section.objects.create(
            chapitre=chapitre,
            titre=content[:190],
            numero=counters['section']
        )
        sous_section = SousSection.objects.create(
            section=section, 
            titre="Contenu", 
            numero=1
        )
        
        # Traitement des enfants
        for child in children:
            process_json_node(
                child, fichier_source, granules_col,
                partie, chapitre, section, sous_section, counters
            )
    
    # NIVEAU 3: GRANULE
    elif node_type in ['granule', 'h3', 'p', 'li', 'div']:
        # Stockage MongoDB (JSON pur)
        granule_mongo = {
            "type": node_type,
            "content": content,
            "html": node.get("html", f"<p>{content}</p>"),
            "fichier_source_id": str(fichier_source.id),
            "metadata": {
                "level": node.get("level", 4),
                "extraction_date": datetime.now().isoformat()
            }
        }
        res = granules_col.insert_one(granule_mongo)
        
        # Stockage MySQL (métadonnées)
        Granule.objects.create(
            sous_section=sous_section,
            fichier_source=fichier_source,
            titre=content[:45] + "..." if len(content) > 45 else content,
            type_contenu="TEXTE",
            mongo_contenu_id=str(res.inserted_id),
            ordre=counters['granule']
        )
        counters['granule'] += 1


# ==============================================================================
# 3. ORCHESTRATEUR PRINCIPAL (Point d'entrée)
# ==============================================================================

def process_and_store_document(fichier_source_instance):
    """
    Point d'entrée principal : orchestre toute la chaîne de traitement.
    """
    try:
        path = fichier_source_instance.fichier_original.path
        ext = os.path.splitext(path)[1].lower().strip('.')
        
        # 1. EXTRACTION → JSON STRUCTURÉ
        print(f"📄 Extraction {ext.upper()} → JSON...")
        if ext == 'docx':
            json_structure = extract_structure_from_docx(path)
        elif ext == 'pdf':
            json_structure = extract_structure_from_pdf(path)
        else:
            raise ValueError(f"Format {ext} non supporté")
        
        if not json_structure.get("sections"):
            raise ValueError("Aucune section extraite du document")
        
        # 2. STOCKAGE MONGODB - DOCUMENT COMPLET
        print(f"💾 Stockage MongoDB fichiers_uploades...")
        mongo_db = get_mongo_db()
        mongo_result = mongo_db['fichiers_uploades'].insert_one({
            "fichier_source_id": str(fichier_source_instance.id),
            "titre": fichier_source_instance.titre,
            "type_original": ext.upper(),
            "structure_json": json_structure,  # 🔥 JSON COMPLET VISIBLE
            "date_traitement": datetime.now().isoformat(),
            "version": "2.0-JSON"
        })
        
        # 3. DÉCOUPAGE ET HIÉRARCHISATION
        print(f"🔨 Création hiérarchie MySQL + granules MongoDB...")
        cours = split_and_create_granules(fichier_source_instance, json_structure)
        
        # 4. FINALISATION
        with transaction.atomic():
            fichier_source_instance.mongo_transforme_id = str(mongo_result.inserted_id)
            fichier_source_instance.statut_traitement = 'TRAITE'
            fichier_source_instance.save()
        
        print(f"✅ Traitement terminé avec succès")
        return True, f"Cours généré : {cours.titre} ({cours.code})"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        with transaction.atomic():
            fichier_source_instance.statut_traitement = 'ERREUR'
            fichier_source_instance.save()
        
        return False, f"Erreur: {str(e)}"