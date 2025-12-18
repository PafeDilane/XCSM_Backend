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

















# xcsm/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

# Vos imports
from .models import FichierSource
from .serializers import FichierSourceSerializer
from .permissions import IsEnseignant
from .processing import process_and_store_document

class DocumentUploadView(generics.CreateAPIView):
    """
    API pour l'upload de documents (PDF/DOCX) et le lancement du processus de transformation.
    URL: /api/v1/documents/upload/
    """
    queryset = FichierSource.objects.all()
    serializer_class = FichierSourceSerializer
    permission_classes = [IsAuthenticated, IsEnseignant] # Sécurité stricte
    parser_classes = (MultiPartParser, FormParser) # Pour gérer les fichiers

    def perform_create(self, serializer):
        # Cette méthode sert uniquement à attacher l'enseignant lors de la sauvegarde
        user = self.request.user
        try:
            # On s'assure que l'utilisateur a bien un profil enseignant
            enseignant = user.profil_enseignant
        except Exception:
            raise PermissionDenied("L'utilisateur connecté n'est pas un enseignant.")
            
        # On sauvegarde juste l'instance dans MySQL
        serializer.save(enseignant=enseignant, statut_traitement='EN_ATTENTE')

    def create(self, request, *args, **kwargs):
        # 1. Validation et Sauvegarde standard
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Récupération de l'instance créée
        instance = serializer.instance
        headers = self.get_success_headers(serializer.data)

        # 2. AUTOMATISATION : Lancement immédiat du traitement
        print(f"🚀 [API] Démarrage du traitement pour : {instance.titre}")
        try:
            succes, message = process_and_store_document(instance)
            
            # 3. Construction de la réponse enrichie
            response_data = serializer.data
            response_data['traitement_automatique'] = {
                "succes": succes,
                "message": message
            }
            
            # Code 201 si tout est OK, 202 si upload OK mais traitement échoué
            status_code = status.HTTP_201_CREATED if succes else status.HTTP_202_ACCEPTED
            
            return Response(response_data, status=status_code, headers=headers)

        except Exception as e:
            # Filet de sécurité ultime
            return Response(
                {
                    "error": "Erreur serveur lors du traitement.", 
                    "detail": str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
