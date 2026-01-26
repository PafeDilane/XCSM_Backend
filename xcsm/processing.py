"""
Moteur de Traitement et de Granulation des Documents (V4.1 - Asynchrone & JSON)

Ce module gère l'extraction sémantique à partir de fichiers PDF et DOCX,
la transformation en structure JSON hiérarchique, et le stockage 
dans MySQL (métadonnées) et MongoDB (contenu riche).
"""
import fitz  # PyMuPDF : Extraction haute performance pour PDF
import os
import re
import mammoth # Conversion DOCX vers HTML propre
import logging
from bs4 import BeautifulSoup # Analyse et nettoyage du HTML
from django.db import transaction
from celery import shared_task
from .utils import get_mongo_db
from .models import FichierSource, Cours, Partie, Chapitre, Section, SousSection, Granule
from datetime import datetime

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. CONVERSION VERS JSON STRUCTURÉ (Cœur de l'extraction)
# ==============================================================================

def extract_structure_from_docx(file_path):
    """
    Convertit un fichier DOCX en structure JSON hiérarchique.
    Utilise Mammoth pour préserver les styles de titres (Heading 1, etc.).
    """
    # On définit un mapping strict pour que Mammoth génère des balises H1, H2, etc.
    style_map = """
    p[style-name='Title'] => h1:fresh
    p[style-name='Heading 1'] => h1:fresh
    p[style-name='Heading 2'] => h2:fresh
    p[style-name='Heading 3'] => h3:fresh
    """
    
    with open(file_path, 'rb') as f:
        # Mammoth produit du HTML propre à partir du flux binaire
        result = mammoth.convert_to_html(f, style_map=style_map)
        html = f"<html><body>{result.value}</body></html>"
    
    # On délègue la transformation HTML -> JSON à la fonction dédiée
    return parse_html_to_json_structure(html)


def extract_structure_from_txt(file_path):
    """
    Convertit un fichier texte simple en structure JSON par simple découpage par paragraphe.
    Chaque ligne non vide devient un paragraphe <p>.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    html_parts = ""
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        html_parts += f"<p>{line}</p>\n"
        
    return parse_html_to_json_structure(f"<html><body>{html_parts}</body></html>")


def extract_structure_from_pdf(file_path):
    """
    Convertit un fichier PDF en JSON structuré par détection heuristique des titres.
    Injecte une gestion d'erreurs robuste pour parer aux fichiers corrompus.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"❌ PDF Corrompu ou illisible : {file_path}. Erreur: {e}")
        raise ValueError("Le format PDF est invalide ou le fichier est corrompu.")

    if len(doc) == 0:
        raise ValueError("Le document PDF est vide.")

    raw_text = ""
    # Agrégation de tout le texte du document
    for page in doc:
        try:
            raw_text += page.get_text("text") + "\n\n--- PAGE BREAK ---\n\n"
        except:
            continue # Saute les pages illisibles
    
    if not raw_text.strip():
        raise ValueError("Aucun texte extractible trouvé dans le PDF.")
    
    # Heuristique : On transforme les blocs de texte en HTML intermédiaire pour réutiliser le parser
    html_parts = ""
    for block in re.split(r'\n\s*\n', raw_text):
        block = block.strip()
        if not block or '--- PAGE' in block:
            continue
        
        # Un titre est souvent une ligne unique et courte
        is_single_line = len(block.split('\n')) == 1
        is_short = len(block) < 150
        
        if is_single_line and is_short:
            if block.isupper():
                html_parts += f"<h1>{block}</h1>\n" # Titre de niveau 1
            elif re.match(r'^[IVX0-9]+\.', block) or block.endswith(':'):
                html_parts += f"<h2>{block}</h2>\n" # Titre de niveau 2
            else:
                html_parts += f"<p>{block}</p>\n"
        else:
            html_parts += f"<p>{block}</p>\n" # Paragraphe standard
    
    return parse_html_to_json_structure(f"<html><body>{html_parts}</body></html>")


def parse_html_to_json_structure(html_content):
    """
    ANALYSEUR SÉMANTIQUE : Transforme un flux HTML en arbre JSON imbriqué.
    Cette fonction crée la hiérarchie parent/enfant nécessaire à la structuration pédagogique.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    root = soup.body if soup.body else soup
    
    structure = {
        "metadata": {
            "extraction_date": datetime.now().isoformat(),
            "version": "2.1-JSON-FR"
        },
        "sections": [] # Liste des chapitres et granules racines
    }
    
    current_h1 = None
    current_h2 = None
    
    for element in root.contents:
        if element.name is None:
            continue # Ignore les nœuds de texte vides (Newlines)
        
        tag = element.name
        text = element.get_text().strip()
        
        if not text:
            continue
        
        # Données du nœud actuel
        node = {
            "type": tag,
            "level": get_semantic_level(tag),
            "content": text,
            "html": str(element),
            "children": [] # Stockage des sous-sections ou granules
        }
        
        # Logique d'imbrication basée sur le niveau H1/H2
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
            # Découpage ligne par ligne pour garantir l'atomicité pédagogique (granulation)
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
                
                # Attachement au parent le plus proche (H2 > H1 > Racine)
                if current_h2:
                    current_h2["children"].append(granule_node)
                elif current_h1:
                    current_h1["children"].append(granule_node)
                else:
                    structure["sections"].append(granule_node)
    
    return structure


def get_semantic_level(tag):
    """Retourne l'importance sémantique d'une balise HTML."""
    levels = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'p': 4, 'li': 4, 'div': 4}
    return levels.get(tag, 5)


# ==============================================================================
# 2. GÉNÉRATION DE LA HIÉRARCHIE (MySQL + MongoDB)
# ==============================================================================

def split_and_create_granules(fichier_source, json_structure):
    """
    Prend la structure JSON et peuple les deux bases de données.
    MySQL : Relations hiérarchiques (Partie->Chapitre->Section).
    MongoDB : Contenu textuel riche des granules individuels.
    """
    mongo_db = get_mongo_db()
    granules_col = mongo_db['granules']
    
    # A. NETTOYAGE de sécurité pour éviter les doublons en cas de re-traitement
    Granule.objects.filter(fichier_source=fichier_source).delete()
    
    # B. CRÉATION DU CONTENEUR COURS
    # Chaque document uploadé devient un "Cours" virtuel
    code_unique = f"C-{fichier_source.id.hex[:6].upper()}"
    cours, _ = Cours.objects.get_or_create(
        code=code_unique,
        defaults={
            'enseignant': fichier_source.enseignant,
            'titre': fichier_source.titre,
            'description': f"Extrait du document: {fichier_source.titre}",
            'est_publie': False
        }
    )
    
    # Réinitialisation forcée de la hiérarchie pour ce cours
    Partie.objects.filter(cours=cours).delete()
    
    # C. INITIALISATION DES OBJETS PAR DÉFAUT (Pour les documents sans titres)
    partie = Partie.objects.create(cours=cours, titre="Contenu Principal", numero=1)
    chapitre = Chapitre.objects.create(partie=partie, titre="Introduction", numero=1)
    section = Section.objects.create(chapitre=chapitre, titre="Généralités", numero=1)
    sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)
    
    counters = {'chapitre': 1, 'section': 1, 'granule': 1}
    
    # D. NAVIGATION RÉCURSIVE DANS L'ARBRE JSON
    for node in json_structure.get("sections", []):
        process_json_node(
            node, fichier_source, granules_col,
            partie, chapitre, section, sous_section, counters
        )
    
    return cours


def process_json_node(node, fichier_source, granules_col, 
                      partie, chapitre, section, sous_section, counters):
    """
    Traite un nœud JSON individuel. 
    S'il s'agit d'un titre, crée les entités MySQL correspondantes.
    S'il s'agit d'un texte, crée le granule MongoDB et MySQL.
    """
    node_type = node.get("type")
    content = node.get("content", "")
    children = node.get("children", [])
    
    # SI TITRE DE NIVEAU 1 -> Nouveau Chapitre
    if node_type == 'h1':
        counters['chapitre'] += 1
        chapitre = Chapitre.objects.create(
            partie=partie,
            titre=content[:190],
            numero=counters['chapitre']
        )
        # Création automatique d'une section par défaut pour accueillir les textes
        section = Section.objects.create(chapitre=chapitre, titre="Début", numero=1)
        sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)
        counters['section'] = 1
        
        # Traitement des sous-éléments (titres h2 ou paragraphes)
        for child in children:
            process_json_node(child, fichier_source, granules_col, partie, chapitre, section, sous_section, counters)
    
    # SI TITRE DE NIVEAU 2 -> Nouvelle Section
    elif node_type == 'h2':
        counters['section'] += 1
        section = Section.objects.create(
            chapitre=chapitre,
            titre=content[:190],
            numero=counters['section']
        )
        sous_section = SousSection.objects.create(section=section, titre="Contenu", numero=1)
        
        for child in children:
            process_json_node(child, fichier_source, granules_col, partie, chapitre, section, sous_section, counters)
    
    # SI TEXTE / GRANULE -> Stockage final
    elif node_type in ['granule', 'h3', 'p', 'li', 'div']:
        # 1. Enregistrement dans MongoDB (Schéma flexible pour texte riche)
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
        
        # 2. Référencement dans MySQL (Pointage vers MongoDB)
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
# 3. ORCHESTRATEUR PRINCIPAL (Point d'entrée Asynchrone)
# ==============================================================================

@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def process_and_store_document_task(self, fichier_source_id):
    """
    Tâche Celery de fond qui exécute l'extraction lourde.
    Permet à l'utilisateur de continuer sa navigation pendant le traitement.
    """
    try:
        fichier_source_instance = FichierSource.objects.get(id=fichier_source_id)
    except FichierSource.DoesNotExist:
        logger.error(f"FichierSource {fichier_source_id} non trouvé.")
        return False

    try:
        path = fichier_source_instance.fichier_original.path
        ext = os.path.splitext(path)[1].lower().strip('.')
        
        # Mise à jour immédiate du statut pour informer le frontend
        fichier_source_instance.statut_traitement = 'EN_COURS'
        fichier_source_instance.save()

        # Étape 1 : Extraction du texte et de la structure
        logger.info(f"📄 Début du traitement {ext.upper()} pour: {fichier_source_instance.titre}")
        
        if ext == 'docx':
            json_structure = extract_structure_from_docx(path)
        elif ext == 'pdf':
            json_structure = extract_structure_from_pdf(path)
        elif ext == 'txt':
            json_structure = extract_structure_from_txt(path)
        else:
            raise ValueError(f"Format {ext} non supporté")

        if not json_structure or not json_structure.get("sections"):
            raise ValueError("Le document semble vide ou illisible.")

        # Étape 2 : Sauvegarde de l'arbre complet dans MongoDB pour consultation future
        mongo_db = get_mongo_db()
        mongodb_res = mongo_db['fichiers_uploades'].insert_one({
            "fichier_source_id": str(fichier_source_instance.id),
            "titre": fichier_source_instance.titre,
            "type_original": ext.upper(),
            "structure_json": json_structure,
            "date_traitement": datetime.now().isoformat()
        })

        # Étape 3 : Découpage sémantique en granules (Peuplement MySQL)
        cours_genere = split_and_create_granules(fichier_source_instance, json_structure)

        # Étape 4 : Finalisation de l'état MySQL
        with transaction.atomic():
            fichier_source_instance.mongo_transforme_id = str(mongodb_res.inserted_id)
            fichier_source_instance.statut_traitement = 'TRAITE'
            fichier_source_instance.type_mime = 'application/json+xcsm'
            fichier_source_instance.save()
            
        logger.info(f"✅ Succès: Document '{fichier_source_instance.titre}' traité.")
        
        # Étape 5 : Notification de l'enseignant (Si le module système le permet)
        try:
            from .notifications.services import NotificationService
            notif_service = NotificationService()
            notif_service.notify_document_processed(
                utilisateur=fichier_source_instance.enseignant.utilisateur,
                fichier_source=fichier_source_instance,
                success=True
            )
        except Exception as e:
            logger.warning(f"Notification ignorée: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement de {fichier_source_id}: {str(e)}")
        
        with transaction.atomic():
            fichier_source_instance.statut_traitement = 'ERREUR'
            fichier_source_instance.save()

        # Envoi d'une notification d'échec
        try:
            from .notifications.services import NotificationService
            notif_service = NotificationService()
            notif_service.notify_document_processed(
                utilisateur=fichier_source_instance.enseignant.utilisateur,
                fichier_source=fichier_source_instance,
                success=False,
                message=str(e)
            )
        except:
            pass

        # Si l'erreur est liée au système de fichiers ou à un timeout, on réessaie plus tard
        if isinstance(e, (IOError, TimeoutError)):
            raise self.retry(exc=e)
            
        return False


def process_and_store_document(instance):
    """
    Lanceur de tâche (Proxy). 
    Utilisé par la vue Django (DocumentUploadView) pour déléguer à Celery.
    """
    process_and_store_document_task.delay(str(instance.id))
    return True, "Le traitement a été délégué au worker Celery."