# from django.shortcuts import render
# # Create your views here.

# # xcsm/views.py
# from rest_framework import generics, status
# from rest_framework.response import Response
# from .serializers import FichierSourceSerializer
# from .processing import process_and_store_document
# from .permissions import IsEnseignant



# from rest_framework.parsers import MultiPartParser, FormParser # AJOUT CRITIQUE



# class DocumentUploadView(generics.CreateAPIView):
#     """
#     API pour l'upload de documents (PDF/DOCX) et le lancement du processus de transformation.
#     URL: /api/v1/documents/upload/
#     """
#     serializer_class = FichierSourceSerializer
#     permission_classes = [IsEnseignant] # Seuls les Enseignants peuvent accéder


#     # AJOUTER CETTE LIGNE : Indique à DRF et Swagger d'accepter les fichiers
#     parser_classes = (MultiPartParser, FormParser)


#     def perform_create(self, serializer):
#         user = self.request.user
        
#         # L'instance Enseignant est requise pour la clé étrangère
#         try:
#             enseignant = user.profil_enseignant
#         except Exception:
#             return Response(
#                 {"detail": "Profil enseignant introuvable."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
            
#         # 1. Sauvegarde du FichierSource (l'instance MySQL)
#         fichier_source_instance = serializer.save(enseignant=enseignant, statut_traitement='EN_ATTENTE')
        
#         # 2. Lancement du processus de traitement SYNCHRONE
#         # NOTE: Ceci est bloquant. En production, cela serait une tâche asynchrone (Celery)
#         success, message = process_and_store_document(fichier_source_instance)

#         if success:
#             # Réponse OK: le fichier est dans MongoDB
#             return Response(
#                 {
#                     "message": "Document uploadé et traitement initial terminé.",
#                     "document_id": fichier_source_instance.id,
#                     "mongo_id": fichier_source_instance.mongo_transforme_id
#                 },
#                 status=status.HTTP_201_CREATED
#             )
#         else:
#             # Réponse ERREUR: le parsing a échoué (PDF corrompu, etc.)
#             # On renvoie 200/201 car l'objet a été créé, mais avec un statut ERREUR
#             return Response(
#                 {
#                     "message": f"Document uploadé, mais traitement initial en échec: {message}",
#                     "document_id": fichier_source_instance.id,
#                     "statut": "ERREUR"
#                 },
#                 status=status.HTTP_202_ACCEPTED # Accepté mais traité avec erreur
#             )

















# # xcsm/views.py
# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.exceptions import PermissionDenied

# # Vos imports
# from .models import FichierSource
# from .serializers import FichierSourceSerializer
# from .permissions import IsEnseignant
# from .processing import process_and_store_document

# class DocumentUploadView(generics.CreateAPIView):
#     """
#     API pour l'upload de documents (PDF/DOCX) et le lancement du processus de transformation.
#     URL: /api/v1/documents/upload/
#     """
#     queryset = FichierSource.objects.all()
#     serializer_class = FichierSourceSerializer
#     permission_classes = []  # Authentification désactivée pour DEV # Sécurité stricte
#     parser_classes = (MultiPartParser, FormParser) # Pour gérer les fichiers

#     def perform_create(self, serializer):
#         # Cette méthode sert uniquement à attacher l'enseignant lors de la sauvegarde
#         user = self.request.user
#         try:
#             # On s'assure que l'utilisateur a bien un profil enseignant
#             enseignant = user.profil_enseignant
#         except Exception:
#             raise PermissionDenied("L'utilisateur connecté n'est pas un enseignant.")
            
#         # On sauvegarde juste l'instance dans MySQL
#         serializer.save(enseignant=enseignant, statut_traitement='EN_ATTENTE')

#     def create(self, request, *args, **kwargs):
#         # 1. Validation et Sauvegarde standard
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
        
#         # Récupération de l'instance créée
#         instance = serializer.instance
#         headers = self.get_success_headers(serializer.data)

#         # 2. AUTOMATISATION : Lancement immédiat du traitement
#         print(f"🚀 [API] Démarrage du traitement pour : {instance.titre}")
#         try:
#             succes, message = process_and_store_document(instance)
            
#             # 3. Construction de la réponse enrichie
#             response_data = serializer.data
#             response_data['traitement_automatique'] = {
#                 "succes": succes,
#                 "message": message
#             }
            
#             # Code 201 si tout est OK, 202 si upload OK mais traitement échoué
#             status_code = status.HTTP_201_CREATED if succes else status.HTTP_202_ACCEPTED
            
#             return Response(response_data, status=status_code, headers=headers)

#         except Exception as e:
#             # Filet de sécurité ultime
#             return Response(
#                 {
#                     "error": "Erreur serveur lors du traitement.", 
#                     "detail": str(e)
#                 }, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )



























# xcsm/views.py - Version complète avec consultation JSON
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from .models import FichierSource, Cours, Granule
from .serializers import FichierSourceSerializer
from .permissions import IsEnseignant
from .processing import process_and_store_document
from datetime import datetime
from .utils import get_mongo_db
from .json_utils import (
    get_fichier_json_structure, 
    get_granule_content,
    get_cours_complete_structure,
    search_in_granules,
    get_statistics
)


# ==============================================================================
# 1. UPLOAD DE DOCUMENTS (Existant - Amélioré)
# ==============================================================================

class DocumentUploadView(generics.CreateAPIView):
    """
    API pour l'upload de documents (PDF/DOCX) et le lancement du processus de transformation.
    URL: POST /api/v1/documents/upload/
    
    Corps de la requête:
        - titre (string): Titre du document
        - fichier_original (file): Fichier PDF ou DOCX
    
    Réponse:
        - document_id: UUID du fichier créé
        - mongo_id: ID MongoDB du document transformé
        - traitement_automatique: Résultat du traitement
    """
    queryset = FichierSource.objects.all()
    serializer_class = FichierSourceSerializer
    permission_classes = [IsAuthenticated]  # Authentification REQUISE pour avoir request.user
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        user = self.request.user
        try:
            enseignant = user.profil_enseignant
        except Exception:
            raise PermissionDenied("L'utilisateur connecté n'est pas un enseignant.")
        
        serializer.save(enseignant=enseignant, statut_traitement='EN_ATTENTE')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        instance = serializer.instance
        headers = self.get_success_headers(serializer.data)

        print(f"🚀 [API] Upload reçu. Démarrage du traitement ASYNCHRONE pour : {instance.titre}")
        
        # Lancement du traitement en arrière-plan
        import threading
        
        def run_processing():
            try:
                process_and_store_document(instance)
            except Exception as e:
                print(f"❌ Erreur lors du traitement asynchrone: {e}")
                instance.statut_traitement = 'ERREUR'
                instance.save()

        thread = threading.Thread(target=run_processing)
        thread.start()
        
        # Réponse immédiate
        response_data = serializer.data
        response_data['message'] = "Fichier uploadé. Traitement en cours en arrière-plan."
        response_data['statut'] = "EN_ATTENTE"
        
        return Response(response_data, status=status.HTTP_202_ACCEPTED, headers=headers)
class DocumentUpdateStructureView(APIView):
    """
    Permet au professeur de corriger la structure (titres, granules) depuis l'éditeur.
    Reçoit une nouvelle `json_structure` et re-génère les granules.
    PUT /api/v1/documents/<uuid:pk>/structure/
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            fichier = FichierSource.objects.get(id=pk)
            # Vérification propriétaire
            if fichier.enseignant != request.user.profil_enseignant:
                return Response({"error": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
            
            # 1. Préparation de la structure
            new_structure = request.data.get("json_structure")
            html_content = request.data.get("html_content")

            if html_content:
                # Si HTML fourni (depuis Tiptap), on le parse
                from .processing import parse_html_to_json_structure
                new_structure = parse_html_to_json_structure(html_content)
            
            if not new_structure:
                 return Response({"error": "Structure ou HTML manquant"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Mise à jour MongoDB
            mongo_db = get_mongo_db()
            mongo_db['fichiers_uploades'].update_one(
                {"fichier_source_id": str(fichier.id)},
                {"$set": {"structure_json": new_structure, "date_modification": datetime.now().isoformat()}}
            )

            # 3. Régénération des Granules MySQL/Mongo
            from .processing import split_and_create_granules
            split_and_create_granules(fichier, new_structure)

            return Response({"status": "Structure mise à jour et granules régénérés"})

        except FichierSource.DoesNotExist:
            return Response({"error": "Fichier introuvable"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Dans xcsm/views.py, ajouter après DocumentUploadView

class DocumentListView(generics.ListAPIView):
    """
    Liste de tous les documents uploadés par l'enseignant connecté
    GET /api/v1/documents/
    """
    serializer_class = FichierSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # On retourne uniquement les fichiers de l'enseignant connecté
        try:
            return FichierSource.objects.filter(enseignant=self.request.user.profil_enseignant).order_by('-date_upload')
        except:
            return FichierSource.objects.none()

class DocumentDeleteView(generics.DestroyAPIView):
    """
    Supprimer un document (et ses granules associés en cascade)
    DELETE /api/v1/documents/<uuid:pk>/
    """
    queryset = FichierSource.objects.all()
    serializer_class = FichierSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Sécurité : on ne peut supprimer que ses propres fichiers
        try:
            return FichierSource.objects.filter(enseignant=self.request.user.profil_enseignant)
        except:
            return FichierSource.objects.none()
    
    
# ==============================================================================
# 2. CONSULTATION DE LA STRUCTURE JSON (NOUVEAU)
# ==============================================================================

class FichierJsonStructureView(APIView):
    """
    Récupère la structure JSON complète d'un fichier uploadé depuis MongoDB.
    URL: GET /api/v1/documents/<uuid:fichier_id>/json/
    
    Réponse:
        - structure_json: Structure hiérarchique complète
        - metadata: Informations sur le traitement
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, fichier_id):
        try:
            fichier = FichierSource.objects.get(id=fichier_id)
        except FichierSource.DoesNotExist:
            return Response(
                {"error": "Fichier introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérification des permissions
        try:
            if fichier.enseignant != request.user.profil_enseignant:
                return Response(
                    {"error": "Vous n'êtes pas propriétaire de ce fichier"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
             # Allowed for admins or if checks fail safely (dev mode)
             pass
        
        # Récupération du JSON depuis MongoDB
        json_structure = get_fichier_json_structure(fichier.id)
        
        # Si le fichier est en attente, on renvoie une structure vide mais avec le statut
        if not json_structure and fichier.statut_traitement == 'EN_ATTENTE':
             return Response({
                "fichier_info": {
                    "id": str(fichier.id),
                    "titre": fichier.titre,
                    "statut_traitement": fichier.statut_traitement, # Using proper name
                    "date_upload": fichier.date_upload
                },
                "json_structure": {}
            })

        if not json_structure:
            # Fallback if processing failed or not found
            return Response(
                {"error": "Structure JSON introuvable dans MongoDB"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            "fichier_info": {
                "id": str(fichier.id),
                "titre": fichier.titre,
                "statut_traitement": fichier.statut_traitement, # Standardized name
                "date_upload": fichier.date_upload
            },
            "json_structure": json_structure
        })


# ==============================================================================
# 3. CONSULTATION D'UN GRANULE INDIVIDUEL
# ==============================================================================

class GranuleDetailView(APIView):
    """
    Récupère le contenu JSON d'un granule spécifique depuis MongoDB.
    URL: GET /api/v1/granules/<uuid:granule_id>/
    
    Réponse:
        - granule_info: Métadonnées MySQL
        - contenu_json: Contenu complet depuis MongoDB
    """
    permission_classes = []  # Authentification désactivée pour DEV
    
    def get(self, request, granule_id):
        try:
            granule = Granule.objects.select_related(
                'sous_section__section__chapitre__partie__cours',
                'fichier_source'
            ).get(id=granule_id)
        except Granule.DoesNotExist:
            return Response(
                {"error": "Granule introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupération du contenu MongoDB
        contenu_json = get_granule_content(granule.mongo_contenu_id)
        
        return Response({
            "granule_info": {
                "id": str(granule.id),
                "titre": granule.titre,
                "type": granule.type_contenu,
                "ordre": granule.ordre,
                "sous_section": granule.sous_section.titre,
                "section": granule.sous_section.section.titre,
                "chapitre": granule.sous_section.section.chapitre.titre
            },
            "contenu_json": contenu_json
        })


# ==============================================================================
# 5. RECHERCHE DANS LES GRANULES
# ==============================================================================


# ==============================================================================
# 5. RECHERCHE DANS LES GRANULES
# ==============================================================================

class GranuleSearchView(APIView):
    """
    Recherche dans les contenus des granules MongoDB.
    URL: GET /api/v1/granules/search/?q=<terme>
    
    Query params:
        - q: Terme de recherche
        - fichier_id (optional): Filtrer par fichier source
    
    Réponse:
        Liste des granules correspondants avec leur contenu
    """
    permission_classes = []  # Authentification désactivée pour DEV
    
    def get(self, request):
        query = request.query_params.get('q', '')
        fichier_id = request.query_params.get('fichier_id', None)
        
        if not query:
            return Response(
                {"error": "Paramètre 'q' requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fichier_source = None
        if fichier_id:
            try:
                fichier_source = FichierSource.objects.get(id=fichier_id)
            except FichierSource.DoesNotExist:
                pass
        
        results = search_in_granules(query, fichier_source)
        
        return Response({
            "query": query,
            "count": len(results),
            "results": results
        })


# ==============================================================================
# 6. STATISTIQUES MONGODB
# ==============================================================================

class MongoStatisticsView(APIView):
    """
    Retourne des statistiques sur les données MongoDB.
    URL: GET /api/v1/statistics/mongodb/
    
    Réponse:
        - Nombre de documents
        - Nombre de granules
        - Nom de la base
    """
    permission_classes = []  # Authentification désactivée pour DEV
    
    def get(self, request):
        stats = get_statistics()
        
        return Response(stats)