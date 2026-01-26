"""
Vues API pour le système de notifications XCSM.
"""
from django.db import models
from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from .models import (
    Notification,
    NotificationPreference,
    PushSubscription,
    NotificationTemplate,
    NotificationDigest
)
from .serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    PushSubscriptionSerializer,
    NotificationTemplateSerializer,
    NotificationDigestSerializer,
    MarkAsReadSerializer,
    BulkNotificationCreateSerializer
)
from .services import NotificationService
from ..permissions import IsAdmin, IsOwnerOrAdmin


class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination standard pour les listes de notifications.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des notifications.

    Endpoints disponibles:
    - GET /notifications/ : Liste des notifications de l'utilisateur
    - GET /notifications/{id}/ : Détail d'une notification
    - PUT /notifications/{id}/ : Mettre à jour une notification
    - DELETE /notifications/{id}/ : Supprimer une notification
    - POST /notifications/mark-as-read/ : Marquer des notifications comme lues
    - POST /notifications/mark-all-read/ : Marquer toutes les notifications comme lues
    - GET /notifications/unread-count/ : Nombre de notifications non lues
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['type_notification', 'est_vue', 'envoyee_in_app']
    ordering_fields = ['date_creation', 'date_lecture']
    ordering = ['-date_creation']
    search_fields = ['titre', 'message']

    def get_queryset(self):
        """
        Retourne uniquement les notifications de l'utilisateur connecté.
        Les administrateurs peuvent voir toutes les notifications.
        """
        user = self.request.user

        if user.type_compte == 'ADMIN':
            # Les administrateurs peuvent voir toutes les notifications
            return Notification.objects.all().select_related(
                'utilisateur', 'fichier_source', 'cours', 'granule'
            )
        else:
            # Les autres utilisateurs ne voient que leurs notifications
            return Notification.objects.filter(
                utilisateur=user
            ).select_related(
                'utilisateur', 'fichier_source', 'cours', 'granule'
            )

    def get_serializer_context(self):
        """
        Ajoute la requête au contexte du serializer.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request):
        """
        Marquer plusieurs notifications comme lues.
        """
        serializer = MarkAsReadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data['notification_ids']

        # Marquer comme lues
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            utilisateur=request.user
        )

        updated_count = 0
        for notification in notifications:
            notification.marquer_comme_vue()
            updated_count += 1

        return Response({
            'message': f'{updated_count} notification(s) marquée(s) comme lue(s)',
            'count': updated_count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Marquer toutes les notifications non lues comme lues.
        """
        notifications = Notification.objects.filter(
            utilisateur=request.user,
            est_vue='NON_VUE'
        )

        count = notifications.count()
        notifications.update(est_vue='VUE', date_lecture=timezone.now())

        return Response({
            'message': f'Toutes les notifications ({count}) ont été marquées comme lues',
            'count': count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Retourne le nombre de notifications non lues.
        """
        count = Notification.objects.filter(
            utilisateur=request.user,
            est_vue='NON_VUE'
        ).count()

        return Response({
            'count': count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='recent', url_name='recent')
    def recent_notifications(self, request):
        """
        Retourne les notifications récentes (7 derniers jours).
        """
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)

        notifications = Notification.objects.filter(
            utilisateur=request.user,
            date_creation__gte=seven_days_ago
        ).order_by('-date_creation')[:10]  # Limiter à 10 résultats

        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='archive', url_name='archive')
    def archive_notification(self, request, pk=None):
        """
        Archiver une notification spécifique.
        """
        notification = self.get_object()
        notification.archiver()

        return Response({
            'message': 'Notification archivée avec succès',
            'notification_id': str(notification.id)
        })


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des préférences de notifications.

    Chaque utilisateur a ses propres préférences.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Un utilisateur ne peut voir que ses propres préférences.
        Les administrateurs peuvent voir toutes les préférences.
        """
        user = self.request.user

        if user.type_compte == 'ADMIN':
            return NotificationPreference.objects.all().select_related('utilisateur')
        else:
            return NotificationPreference.objects.filter(utilisateur=user).select_related('utilisateur')

    def get_object(self):
        """
        Retourne les préférences de l'utilisateur connecté.
        """
        if self.request.user.type_compte == 'ADMIN' and 'pk' in self.kwargs:
            # Les admins peuvent accéder à n'importe quelle préférence via l'ID
            return super().get_object()

        # Pour les non-admins, retourner toujours leurs propres préférences
        preference, created = NotificationPreference.objects.get_or_create(
            utilisateur=self.request.user
        )
        return preference

    def create(self, request, *args, **kwargs):
        """
        Empêcher la création multiple.
        """
        # Vérifier si des préférences existent déjà
        existing = NotificationPreference.objects.filter(
            utilisateur=request.user
        ).first()

        if existing:
            return Response({
                'error': 'Des préférences existent déjà pour cet utilisateur',
                'preference_id': str(existing.id)
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='mine', url_name='mine')
    def my_preferences(self, request):
        """
        Retourne les préférences de l'utilisateur connecté.
        """
        preference, created = NotificationPreference.objects.get_or_create(
            utilisateur=request.user
        )
        serializer = self.get_serializer(preference)
        return Response(serializer.data)


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des abonnements push.

    Permet aux utilisateurs de gérer leurs abonnements aux notifications push.
    """
    serializer_class = PushSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retourne les abonnements de l'utilisateur connecté.
        """
        return PushSubscription.objects.filter(
            utilisateur=self.request.user,
            is_active=True
        )

    def perform_create(self, serializer):
        """
        Associer automatiquement l'utilisateur connecté.
        """
        serializer.save(utilisateur=self.request.user)

    @action(detail=False, methods=['post'], url_path='unsubscribe')
    def unsubscribe(self, request):
        """
        Désinscrire un appareil spécifique.
        """
        device_id = request.data.get('device_id')

        if not device_id:
            return Response({
                'error': 'Le device_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        subscription = PushSubscription.objects.filter(
            device_id=device_id,
            utilisateur=request.user
        ).first()

        if not subscription:
            return Response({
                'error': 'Abonnement non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

        subscription.desactiver()

        return Response({
            'message': 'Appareil désinscrit avec succès',
            'device_id': device_id
        })


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des templates de notifications.

    Réservé aux administrateurs.
    """
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = NotificationTemplate.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type_notification', 'is_active']
    search_fields = ['code', 'nom']

    @action(detail=True, methods=['post'], url_path='test', url_name='test')
    def test_template(self, request, pk=None):
        """
        Tester un template avec des données de test.
        """
        template = self.get_object()
        test_data = request.data.get('context', {})

        try:
            # Rendu du template
            email_sujet, email_html, email_text = template.render_email(test_data)
            push_titre, push_message = template.render_push(test_data)
            in_app_titre, in_app_message = template.render_in_app(test_data)

            return Response({
                'email': {
                    'sujet': email_sujet,
                    'html_preview': email_html[:500] + '...' if len(email_html) > 500 else email_html,
                    'text_preview': email_text[:500] + '...' if len(email_text) > 500 else email_text
                },
                'push': {
                    'titre': push_titre,
                    'message': push_message
                },
                'in_app': {
                    'titre': in_app_titre,
                    'message': in_app_message
                }
            })
        except Exception as e:
            return Response({
                'error': f'Erreur lors du rendu du template: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class NotificationDigestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les synthèses de notifications.

    Les utilisateurs ne peuvent voir que leurs propres synthèses.
    """
    serializer_class = NotificationDigestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Retourne les synthèses de l'utilisateur connecté.
        """
        return NotificationDigest.objects.filter(
            utilisateur=self.request.user
        ).prefetch_related('notifications').order_by('-date_creation')


class BulkNotificationCreateView(generics.CreateAPIView):
    """
    Vue pour créer des notifications en masse.

    Réservé aux administrateurs et enseignants.
    """
    serializer_class = BulkNotificationCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Créer des notifications pour plusieurs utilisateurs.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Vérifier les permissions
        user = request.user
        if user.type_compte not in ['ADMIN', 'ENSEIGNANT']:
            return Response({
                'error': 'Vous n\'avez pas la permission de créer des notifications en masse'
            }, status=status.HTTP_403_FORBIDDEN)

        data = serializer.validated_data

        # Créer les notifications via le service
        notification_service = NotificationService()
        created_count = 0

        for user_id in data['utilisateur_ids']:
            try:
                # Récupérer l'utilisateur
                from xcsm.models import Utilisateur
                utilisateur = Utilisateur.objects.get(id=user_id)

                # Créer la notification
                notification = Notification.objects.create(
                    utilisateur=utilisateur,
                    type_notification=data['type_notification'],
                    titre=data['titre'],
                    message=data['message'],
                    metadata=data.get('metadata', {}),
                    envoyee_email=data['envoyer_email'],
                    envoyee_push=data['envoyer_push'],
                    envoyee_in_app=data['envoyer_in_app']
                )

                # Envoyer via les canaux sélectionnés (asynchrone)
                if data['envoyer_email']:
                    notification_service.send_notification_email(notification)

                if data['envoyer_push']:
                    notification_service.send_push_notification(notification)

                created_count += 1

            except Exception as e:
                # Continuer avec les autres utilisateurs en cas d'erreur
                print(f"Erreur lors de la création de notification pour l'utilisateur {user_id}: {str(e)}")
                continue

        return Response({
            'message': f'{created_count} notification(s) créée(s) avec succès',
            'count': created_count,
            'total_users': len(data['utilisateur_ids'])
        }, status=status.HTTP_201_CREATED)


class NotificationStatsView(generics.GenericAPIView):
    """
    Vue pour les statistiques des notifications.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retourne des statistiques sur les notifications.
        """
        user = request.user

        if user.type_compte == 'ADMIN':
            # Statistiques globales pour les admins
            total_notifications = Notification.objects.count()
            unread_count = Notification.objects.filter(est_vue='NON_VUE').count()
            read_count = Notification.objects.filter(est_vue='VUE').count()
            archived_count = Notification.objects.filter(est_vue='ARCHIVEE').count()

            # Par type
            by_type = Notification.objects.values('type_notification').annotate(
                count=models.Count('id')
            )

            # Par canal
            email_count = Notification.objects.filter(envoyee_email=True).count()
            push_count = Notification.objects.filter(envoyee_push=True).count()
            in_app_count = Notification.objects.filter(envoyee_in_app=True).count()

            stats = {
                'global': {
                    'total': total_notifications,
                    'unread': unread_count,
                    'read': read_count,
                    'archived': archived_count,
                    'read_rate': (read_count / total_notifications * 100) if total_notifications > 0 else 0
                },
                'by_type': list(by_type),
                'by_channel': {
                    'email': email_count,
                    'push': push_count,
                    'in_app': in_app_count
                }
            }
        else:
            # Statistiques personnelles
            user_notifications = Notification.objects.filter(utilisateur=user)
            total_notifications = user_notifications.count()
            unread_count = user_notifications.filter(est_vue='NON_VUE').count()
            read_count = user_notifications.filter(est_vue='VUE').count()

            # Dernière semaine
            seven_days_ago = timezone.now() - timezone.timedelta(days=7)
            recent_count = user_notifications.filter(
                date_creation__gte=seven_days_ago
            ).count()

            stats = {
                'personal': {
                    'total': total_notifications,
                    'unread': unread_count,
                    'read': read_count,
                    'recent_7_days': recent_count
                }
            }

        return Response(stats)