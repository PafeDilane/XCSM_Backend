"""
Serializers Django REST Framework pour les notifications.
"""
from rest_framework import serializers
from .models import (
    Notification,
    NotificationPreference,
    PushSubscription,
    NotificationTemplate,
    NotificationDigest
)
from xcsm.models import Utilisateur


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour les notifications.
    """
    utilisateur_nom = serializers.CharField(
        source='utilisateur.get_full_name',
        read_only=True
    )
    utilisateur_username = serializers.CharField(
        source='utilisateur.username',
        read_only=True
    )
    type_notification_display = serializers.CharField(
        source='get_type_notification_display',
        read_only=True
    )
    est_vue_display = serializers.CharField(
        source='get_est_vue_display',
        read_only=True
    )

    # URLs des objets liés (si disponibles)
    fichier_source_url = serializers.SerializerMethodField()
    cours_url = serializers.SerializerMethodField()
    granule_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'utilisateur', 'utilisateur_nom', 'utilisateur_username',
            'type_notification', 'type_notification_display',
            'titre', 'message', 'metadata',
            'est_vue', 'est_vue_display',
            'envoyee_email', 'envoyee_push', 'envoyee_in_app',
            'fichier_source', 'cours', 'granule',
            'fichier_source_url', 'cours_url', 'granule_url',
            'date_creation', 'date_envoi', 'date_lecture', 'date_archivage',
            'email_statut', 'push_statut',
        ]
        read_only_fields = [
            'id', 'date_creation', 'date_envoi', 'date_lecture', 'date_archivage',
            'email_statut', 'push_statut'
        ]

    def get_fichier_source_url(self, obj):
        """
        Retourne l'URL du fichier source si disponible.
        """
        if obj.fichier_source:
            return f"/api/v1/documents/{obj.fichier_source.id}/json/"
        return None

    def get_cours_url(self, obj):
        """
        Retourne l'URL du cours si disponible.
        """
        if obj.cours:
            return f"/api/v1/cours/{obj.cours.id}/export-json/"
        return None

    def get_granule_url(self, obj):
        """
        Retourne l'URL du granule si disponible.
        """
        if obj.granule:
            return f"/api/v1/granules/{obj.granule.id}/"
        return None

    def validate(self, data):
        """
        Validation des données.
        """
        # S'assurer qu'au moins un canal est sélectionné
        channels_selected = any([
            data.get('envoyee_email', False),
            data.get('envoyee_push', False),
            data.get('envoyee_in_app', False)
        ])

        if not channels_selected:
            raise serializers.ValidationError(
                "Au moins un canal doit être sélectionné pour l'envoi."
            )

        return data


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de notifications.
    Simplifié pour l'usage interne.
    """
    class Meta:
        model = Notification
        fields = [
            'utilisateur',
            'type_notification',
            'titre',
            'message',
            'metadata',
            'fichier_source',
            'cours',
            'granule',
            'envoyee_email',
            'envoyee_push',
            'envoyee_in_app',
        ]

    def create(self, validated_data):
        """
        Création d'une notification avec gestion automatique de certains champs.
        """
        # Forcer l'envoi in-app si aucun canal n'est spécifié
        if not any([validated_data.get('envoyee_email', False),
                    validated_data.get('envoyee_push', False),
                    validated_data.get('envoyee_in_app', False)]):
            validated_data['envoyee_in_app'] = True

        notification = Notification.objects.create(**validated_data)
        return notification


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer pour les préférences de notifications.
    """
    utilisateur_nom = serializers.CharField(
        source='utilisateur.get_full_name',
        read_only=True
    )
    digest_frequency_display = serializers.CharField(
        source='get_digest_frequency_display',
        read_only=True
    )

    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'utilisateur', 'utilisateur_nom',
            # Préférences par type
            'document_traite_email', 'document_traite_push', 'document_traite_in_app',
            'document_erreur_email', 'document_erreur_push', 'document_erreur_in_app',
            'nouvelle_evaluation_email', 'nouvelle_evaluation_push', 'nouvelle_evaluation_in_app',
            'evaluation_corrigee_email', 'evaluation_corrigee_push', 'evaluation_corrigee_in_app',
            'nouveau_message_email', 'nouveau_message_push', 'nouveau_message_in_app',
            'system_maintenance_email', 'system_maintenance_push', 'system_maintenance_in_app',
            # Paramètres globaux
            'email_notifications_enabled',
            'push_notifications_enabled',
            'in_app_notifications_enabled',
            'digest_frequency', 'digest_frequency_display',
            # Dates
            'date_creation', 'date_mise_a_jour',
        ]
        read_only_fields = ['id', 'date_creation', 'date_mise_a_jour']


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les abonnements push.
    """
    utilisateur_nom = serializers.CharField(
        source='utilisateur.get_full_name',
        read_only=True
    )
    device_type_display = serializers.CharField(
        source='get_device_type_display',
        read_only=True
    )

    class Meta:
        model = PushSubscription
        fields = [
            'id',
            'utilisateur', 'utilisateur_nom',
            'device_type', 'device_type_display',
            'device_id', 'device_name', 'device_model',
            'subscription_data',
            'vapid_public_key', 'vapid_private_key',
            'is_active',
            'last_seen',
            'date_creation', 'date_desactivation',
        ]
        read_only_fields = [
            'id', 'date_creation', 'date_desactivation', 'last_seen'
        ]

    def validate_subscription_data(self, value):
        """
        Validation des données d'abonnement.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Les données d'abonnement doivent être un objet JSON."
            )

        # Validation spécifique selon le type de device
        device_type = self.initial_data.get('device_type')

        if device_type == 'WEB':
            # Pour Web Push, vérifier la présence des clés
            required_keys = ['endpoint', 'keys']
            for key in required_keys:
                if key not in value:
                    raise serializers.ValidationError(
                        f"Clé '{key}' manquante pour les abonnements WEB."
                    )

            if 'keys' in value:
                keys_required = ['p256dh', 'auth']
                for key in keys_required:
                    if key not in value['keys']:
                        raise serializers.ValidationError(
                            f"Clé '{key}' manquante dans les keys pour les abonnements WEB."
                        )

        elif device_type in ['ANDROID', 'IOS']:
            # Pour mobile, vérifier la présence du token
            if 'token' not in value:
                raise serializers.ValidationError(
                    "Token manquant pour les abonnements mobiles."
                )

        return value

    def create(self, validated_data):
        """
        Création d'un abonnement push.
        """
        # Vérifier si un abonnement existe déjà pour cet appareil
        device_id = validated_data.get('device_id')
        utilisateur = validated_data.get('utilisateur')

        existing = PushSubscription.objects.filter(
            device_id=device_id,
            utilisateur=utilisateur
        ).first()

        if existing:
            # Mettre à jour l'abonnement existant
            existing.subscription_data = validated_data.get('subscription_data')
            existing.device_name = validated_data.get('device_name')
            existing.device_model = validated_data.get('device_model')
            existing.is_active = True
            existing.save()
            return existing

        # Créer un nouvel abonnement
        return super().create(validated_data)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer pour les templates de notifications.
    """
    type_notification_display = serializers.CharField(
        source='get_type_notification_display',
        read_only=True
    )

    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'code', 'nom',
            'type_notification', 'type_notification_display',
            'template_email_sujet', 'template_email_html', 'template_email_text',
            'template_push_titre', 'template_push_message',
            'template_in_app_titre', 'template_in_app_message',
            'variables_disponibles',
            'is_active',
            'date_creation', 'date_mise_a_jour',
        ]
        read_only_fields = ['id', 'date_creation', 'date_mise_a_jour']


class NotificationDigestSerializer(serializers.ModelSerializer):
    """
    Serializer pour les synthèses de notifications.
    """
    utilisateur_nom = serializers.CharField(
        source='utilisateur.get_full_name',
        read_only=True
    )
    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )
    notifications_incluses = NotificationSerializer(
        source='notifications',
        many=True,
        read_only=True
    )

    class Meta:
        model = NotificationDigest
        fields = [
            'id',
            'utilisateur', 'utilisateur_nom',
            'notifications', 'notifications_incluses',
            'contenu_html', 'contenu_text',
            'statut', 'statut_display',
            'email_message_id',
            'email_ouvert', 'email_clique',
            'date_creation', 'date_envoi', 'date_ouverture', 'date_clic',
        ]
        read_only_fields = [
            'id', 'date_creation', 'date_envoi',
            'date_ouverture', 'date_clic'
        ]


class MarkAsReadSerializer(serializers.Serializer):
    """
    Serializer pour marquer des notifications comme lues.
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="Liste des IDs des notifications à marquer comme lues"
    )

    def validate_notification_ids(self, value):
        """
        Validation des IDs de notification.
        """
        if not value:
            raise serializers.ValidationError(
                "La liste des IDs ne peut pas être vide."
            )

        # Vérifier que l'utilisateur peut accéder à ces notifications
        user = self.context['request'].user
        accessible_notifications = Notification.objects.filter(
            id__in=value,
            utilisateur=user
        ).values_list('id', flat=True)

        inaccessible_ids = set(value) - set(accessible_notifications)
        if inaccessible_ids:
            raise serializers.ValidationError(
                f"Vous n'avez pas accès aux notifications avec les IDs: {inaccessible_ids}"
            )

        return value


class BulkNotificationCreateSerializer(serializers.Serializer):
    """
    Serializer pour créer plusieurs notifications en une seule requête.
    """
    utilisateur_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="Liste des IDs des utilisateurs destinataires"
    )
    type_notification = serializers.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        required=True
    )
    titre = serializers.CharField(max_length=200, required=True)
    message = serializers.CharField(required=True)
    metadata = serializers.JSONField(required=False, default=dict)
    envoyer_email = serializers.BooleanField(default=False)
    envoyer_push = serializers.BooleanField(default=False)
    envoyer_in_app = serializers.BooleanField(default=True)

    def validate_utilisateur_ids(self, value):
        """
        Validation des IDs utilisateur.
        """
        if not value:
            raise serializers.ValidationError(
                "La liste des IDs utilisateur ne peut pas être vide."
            )

        # Vérifier que les utilisateurs existent
        existing_users = Utilisateur.objects.filter(
            id__in=value
        ).values_list('id', flat=True)

        non_existent_ids = set(value) - set(existing_users)
        if non_existent_ids:
            raise serializers.ValidationError(
                f"Utilisateurs non trouvés avec les IDs: {non_existent_ids}"
            )

        return value