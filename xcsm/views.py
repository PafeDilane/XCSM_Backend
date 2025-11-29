from django.shortcuts import render
# Create your views here.

# xcsm/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import FichierSourceSerializer
from .processing import process_and_store_document
from .permissions import IsEnseignant



from rest_framework.parsers import MultiPartParser, FormParser # AJOUT CRITIQUE



class DocumentUploadView(generics.CreateAPIView):
    """
    API pour l'upload de documents (PDF/DOCX) et le lancement du processus de transformation.
    URL: /api/v1/documents/upload/
    """
    serializer_class = FichierSourceSerializer
    permission_classes = [IsEnseignant] # Seuls les Enseignants peuvent accéder


    # AJOUTER CETTE LIGNE : Indique à DRF et Swagger d'accepter les fichiers
    parser_classes = (MultiPartParser, FormParser)


    def perform_create(self, serializer):
        user = self.request.user
        
        # L'instance Enseignant est requise pour la clé étrangère
        try:
            enseignant = user.profil_enseignant
        except Exception:
            return Response(
                {"detail": "Profil enseignant introuvable."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 1. Sauvegarde du FichierSource (l'instance MySQL)
        fichier_source_instance = serializer.save(enseignant=enseignant, statut_traitement='EN_ATTENTE')
        
        # 2. Lancement du processus de traitement SYNCHRONE
        # NOTE: Ceci est bloquant. En production, cela serait une tâche asynchrone (Celery)
        success, message = process_and_store_document(fichier_source_instance)

        if success:
            # Réponse OK: le fichier est dans MongoDB
            return Response(
                {
                    "message": "Document uploadé et traitement initial terminé.",
                    "document_id": fichier_source_instance.id,
                    "mongo_id": fichier_source_instance.mongo_transforme_id
                },
                status=status.HTTP_201_CREATED
            )
        else:
            # Réponse ERREUR: le parsing a échoué (PDF corrompu, etc.)
            # On renvoie 200/201 car l'objet a été créé, mais avec un statut ERREUR
            return Response(
                {
                    "message": f"Document uploadé, mais traitement initial en échec: {message}",
                    "document_id": fichier_source_instance.id,
                    "statut": "ERREUR"
                },
                status=status.HTTP_202_ACCEPTED # Accepté mais traité avec erreur
            )
