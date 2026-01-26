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
#     permission_classes = [IsAuthenticated, IsEnseignant] # Sécurité stricte
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
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from .models import FichierSource, Cours, Granule, ActionLog, Evaluation, Correction
from .serializers import FichierSourceSerializer, ActionLogSerializer, CoursSerializer, EvaluationSerializer, CorrectionSerializer
from .permissions import IsEnseignant
from .processing import process_and_store_document
from .json_utils import (
    get_fichier_json_structure, 
    get_granule_content,
    get_cours_complete_structure,
    search_in_granules,
    get_statistics
)

class CoursViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des cours.
    UC09a/11a/12a
    """
    serializer_class = CoursSerializer
    permission_classes = [IsAuthenticated, IsEnseignant]

    def get_queryset(self):
        if self.request.user.type_compte == 'ETUDIANT':
            # Les étudiants ne voient que les cours publiés
            return Cours.objects.filter(est_publie=True)
        return Cours.objects.filter(enseignant__utilisateur=self.request.user)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """ UC12a: Publier un cours """
        cours = self.get_object()
        # Validation UC12a: Min 5 granulés recommandés (ou requis selon interprétation)
        # On vérifie la profondeur via SousSection > Granule
        nb_granules = Granule.objects.filter(sous_section__section__chapitre__partie__cours=cours).count()
        
        if nb_granules < 5:
            return Response(
                {"error": f"Le cours doit contenir au moins 5 granulés pour être publié (Actuel: {nb_granules})."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cours.est_publie = True
        cours.save()
        return Response({"status": "Cours publié avec succès."})


class EvaluationViewSet(viewsets.ModelViewSet):
    """ UC09b/11b/12b """
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated, IsEnseignant]

    def get_queryset(self):
        return Evaluation.objects.filter(cours__enseignant__utilisateur=self.request.user)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        eval_obj = self.get_object()
        if not eval_obj.cours.est_publie:
            return Response({"error": "Le cours associé doit être publié avant l'évaluation."}, status=status.HTTP_400_BAD_REQUEST)
        eval_obj.est_publie = True
        eval_obj.date_publication = timezone.now()
        eval_obj.save()
        return Response({"status": "Évaluation publiée."})


class CorrectionViewSet(viewsets.ModelViewSet):
    """ UC09c/11c/12c """
    serializer_class = CorrectionSerializer
    permission_classes = [IsAuthenticated, IsEnseignant]

    def get_queryset(self):
        return Correction.objects.filter(evaluation__cours__enseignant__utilisateur=self.request.user)
from .permissions import IsEnseignant
from .processing import process_and_store_document
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
    permission_classes = [IsAuthenticated, IsEnseignant]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        user = self.request.user
        enseignant = getattr(self.request.user, 'profil_enseignant', None)
        if not enseignant:
            raise PermissionDenied("L'utilisateur n'est pas un enseignant.")
        
        serializer.save(enseignant=enseignant, statut_traitement='EN_ATTENTE')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        instance = serializer.instance
        headers = self.get_success_headers(serializer.data)

        print(f"🚀 [API] Démarrage du traitement JSON pour : {instance.titre}")
        try:
            succes, message = process_and_store_document(instance)
            
            response_data = serializer.data
            response_data['traitement_automatique'] = {
                "succes": succes,
                "message": message,
                "type_traitement": "JSON-Structuré"
            }
            
            status_code = status.HTTP_201_CREATED if succes else status.HTTP_202_ACCEPTED
            
            return Response(response_data, status=status_code, headers=headers)

        except Exception as e:
            return Response(
                {
                    "error": "Erreur serveur lors du traitement.", 
                    "detail": str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FichierSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des fichiers sources.
    UC06: Consulter liste des uploads.
    UC07: Supprimer un document.
    """
    serializer_class = FichierSourceSerializer
    permission_classes = [IsAuthenticated, IsEnseignant]

    def get_queryset(self):
        # Un enseignant ne voit que ses propres uploads
        return FichierSource.objects.filter(enseignant__utilisateur=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # UC07: Vérifier les dépendances avant suppression
        instance = self.get_object()
        
        # Vérifier si des granules issus de ce fichier sont utilisés dans des cours publiés
        granules_ids = instance.granules_extraits.values_list('id', flat=True)
        # On pourrait complexifier ici en vérifiant les jointures avec Cours/Partie/...
        # Mais pour cette phase, on applique la suppression en cascade demandée.
        
        # Log de suppression (déjà géré par le signal post_delete)
        return super().destroy(request, *args, **kwargs)


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
        if not request.user.is_staff:
            if not hasattr(request.user, 'profil_enseignant'):
                return Response(
                    {"error": "Permission refusée"},
                    status=status.HTTP_403_FORBIDDEN
                )
            if fichier.enseignant != request.user.profil_enseignant:
                return Response(
                    {"error": "Vous n'êtes pas propriétaire de ce fichier"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Récupération du JSON depuis MongoDB
        json_structure = get_fichier_json_structure(fichier.id)
        
        if not json_structure:
            return Response(
                {"error": "Structure JSON introuvable dans MongoDB"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            "fichier_info": {
                "id": str(fichier.id),
                "titre": fichier.titre,
                "statut": fichier.statut_traitement,
                "date_upload": fichier.date_upload
            },
            "json_structure": json_structure
        })


# ==============================================================================
# 3. CONSULTATION D'UN GRANULE INDIVIDUEL
# ==============================================================================

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        cr = self.get_object()
        if not cr.evaluation.est_publie:
            return Response({"error": "L'évaluation associée doit être publiée."}, status=status.HTTP_400_BAD_REQUEST)
        cr.est_publie = True
        cr.save()
        return Response({"status": "Correction publiée."})


class GranuleDetailView(APIView):
    """
    Récupère ou modifie le contenu d'un granule.
    UC10: Corriger granulés.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, granule_id):
        try:
            return Granule.objects.get(id=granule_id)
        except Granule.DoesNotExist:
            return None

    def get(self, request, granule_id):
        granule = self.get_object(granule_id)
        if not granule:
            return Response({"error": "Granule introuvable"}, status=status.HTTP_404_NOT_FOUND)
        
        contenu_json = get_granule_content(granule.mongo_contenu_id)
        return Response({
            "granule_info": {
                "id": str(granule.id),
                "titre": granule.titre,
                "type": granule.type_contenu,
                "ordre": granule.ordre
            },
            "contenu_json": contenu_json
        })

    def put(self, request, granule_id):
        return self.patch(request, granule_id)

    def patch(self, request, granule_id):
        granule = self.get_object(granule_id)
        if not granule:
            return Response({"error": "Granule introuvable"}, status=status.HTTP_404_NOT_FOUND)
            
        # Vérification propriétaire (via FichierSource)
        if not request.user.is_staff and granule.fichier_source.enseignant.utilisateur != request.user:
            return Response({"error": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        # 1. Mise à jour Métadonnées MySQL
        if 'titre' in request.data:
            granule.titre = request.data['titre']
        if 'ordre' in request.data:
            granule.ordre = request.data['ordre']
        granule.save()

        # 2. Mise à jour MongoDB
        from .json_utils import update_granule_content
        # On passe tout le corps de la requête à Mongo (content, html, etc.)
        success = update_granule_content(granule.mongo_contenu_id, request.data)
        
        if success:
            return Response({"message": "Granule mis à jour avec succès"})
        return Response({"error": "Erreur lors de la mise à jour MongoDB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==============================================================================
# 4. EXPORT COMPLET D'UN COURS EN JSON
# ==============================================================================

class CoursJsonExportView(APIView):
    """
    Exporte la structure complète d'un cours avec tous ses granules en JSON.
    URL: GET /api/v1/cours/<uuid:cours_id>/export-json/
    
    Réponse:
        Structure hiérarchique complète du cours
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, cours_id):
        try:
            cours = Cours.objects.select_related('enseignant').get(id=cours_id)
        except Cours.DoesNotExist:
            return Response(
                {"error": "Cours introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérification des permissions
        if not request.user.is_staff:
            if not hasattr(request.user, 'profil_enseignant'):
                return Response(
                    {"error": "Permission refusée"},
                    status=status.HTTP_403_FORBIDDEN
                )
            if cours.enseignant != request.user.profil_enseignant:
                return Response(
                    {"error": "Vous n'êtes pas propriétaire de ce cours"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Génération de la structure complète
        structure_complete = get_cours_complete_structure(cours)
        
        return Response(structure_complete)


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
    permission_classes = [IsAuthenticated]
    
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Réservé aux administrateurs"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = get_statistics()
        
        return Response(stats)


from rest_framework import viewsets

class ActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour la consultation de l'historique des actions.
    UC08: Consulter historique.
    """
    serializer_class = ActionLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.type_compte == 'ADMIN':
            return ActionLog.objects.all()
        return ActionLog.objects.filter(utilisateur=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        action_type = request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
            
        period = request.query_params.get('period')
        if period == '7':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timezone.timedelta(days=7))
        elif period == '30':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timezone.timedelta(days=30))
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudentPortalView(APIView):
    """
    Vue unifiée pour les étudiants.
    UC13: Consulter documents.
    Retourne les Cours, Évaluations et Corrections publiés et adaptés au niveau/filière.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Par défaut, on filtre par le profil de l'étudiant (si c'est un étudiant)
        # Sinon (Enseignant/Admin), on peut voir tout ce qui est publié.
        
        niveau = request.query_params.get('niveau')
        filiere = request.query_params.get('filiere')
        doc_type = request.query_params.get('type') # 'cours', 'eval', 'corr'

        if not niveau and hasattr(user, 'profil_etudiant'):
            niveau = user.profil_etudiant.niveau
        if not filiere and hasattr(user, 'profil_etudiant'):
            filiere = user.profil_etudiant.filiere

        results = []

        # 1. Récupération des COURS
        if not doc_type or doc_type == 'cours':
            cours_qs = Cours.objects.filter(est_publie=True)
            if niveau: cours_qs = cours_qs.filter(niveau=niveau)
            if filiere: cours_qs = cours_qs.filter(filiere__icontains=filiere)
            
            for c in cours_qs:
                results.append({
                    'id': str(c.id),
                    'titre': c.titre,
                    'code': c.code,
                    'type': 'Cours',
                    'badge_color': 'blue',
                    'enseignant': c.enseignant.utilisateur.get_full_name() or c.enseignant.utilisateur.username,
                    'description': c.description[:200],
                    'nb_granules': Granule.objects.filter(sous_section__section__chapitre__partie__cours=c).count(),
                    'date_publication': c.date_creation, # à affiner si champ dédié
                    'statut_acces': 'Accessible'
                })

        # 2. Récupération des EVALUATIONS
        if not doc_type or doc_type == 'eval':
            eval_qs = Evaluation.objects.filter(est_publie=True)
            if niveau: eval_qs = eval_qs.filter(cours__niveau=niveau)
            
            for e in eval_qs:
                results.append({
                    'id': str(e.id),
                    'titre': e.titre,
                    'code': e.code,
                    'type': 'Evaluation',
                    'badge_color': 'orange',
                    'enseignant': e.cours.enseignant.utilisateur.get_full_name(),
                    'description': e.description[:200],
                    'duree': e.duree,
                    'date_publication': e.date_publication,
                    'statut_acces': 'Accessible'
                })

        # 3. Récupération des CORRECTIONS
        if not doc_type or doc_type == 'corr':
            corr_qs = Correction.objects.filter(est_publie=True)
            if niveau: corr_qs = corr_qs.filter(evaluation__cours__niveau=niveau)
            
            for cr in corr_qs:
                results.append({
                    'id': str(cr.id),
                    'titre': cr.titre,
                    'code': cr.code,
                    'type': 'Correction',
                    'badge_color': 'green',
                    'enseignant': cr.evaluation.cours.enseignant.utilisateur.get_full_name(),
                    'date_publication': cr.date_creation,
                    'statut_acces': 'Accessible'
                })

        # Tri par date de publication (décroissant)
        results.sort(key=lambda x: x.get('date_publication') or timezone.now(), reverse=True)

        return Response({
            "count": len(results),
            "results": results,
            "filters_applied": {
                "niveau": niveau,
                "filiere": filiere,
                "type": doc_type
            }
        })