"""
Modèles de données pour le système de notifications XCSM.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

from xcsm.models import Utilisateur, Enseignant, Etudiant, Administrateur
from xcsm.models import FichierSource, Cours, Granule


class NotificationPreference(models.Model):
    """
    Préférences de notification par utilisateur.
    Permet à chaque utilisateur de configurer quelles notifications il souhaite recevoir et par quel canal.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='preferences_notifications'
    )

    # Préférences par type de notification
    document_traite_email = models.BooleanField(default=True, verbose_name="Document traité - Email")
    document_traite_push = models.BooleanField(default=False, verbose_name="Document traité - Push")
    document_traite_in_app = models.BooleanField(default=True, verbose_name="Document traité - In-App")

    document_erreur_email = models.BooleanField(default=True, verbose_name="Erreur traitement - Email")
    document_erreur_push = models.BooleanField(default=True, verbose_name="Erreur traitement - Push")
    document_erreur_in_app = models.BooleanField(default=True, verbose_name="Erreur traitement - In-App")

    nouvelle_evaluation_email = models.BooleanField(default=True, verbose_name="Nouvelle évaluation - Email")
    nouvelle_evaluation_push = models.BooleanField(default=True, verbose_name="Nouvelle évaluation - Push")
    nouvelle_evaluation_in_app = models.BooleanField(default=True, verbose_name="Nouvelle évaluation - In-App")

    evaluation_corrigee_email = models.BooleanField(default=True, verbose_name="Évaluation corrigée - Email")
    evaluation_corrigee_push = models.BooleanField(default=False, verbose_name="Évaluation corrigée - Push")
    evaluation_corrigee_in_app = models.BooleanField(default=True, verbose_name="Évaluation corrigée - In-App")

    nouveau_message_email = models.BooleanField(default=False, verbose_name="Nouveau message - Email")
    nouveau_message_push = models.BooleanField(default=True, verbose_name="Nouveau message - Push")
    nouveau_message_in_app = models.BooleanField(default=True, verbose_name="Nouveau message - In-App")

    system_maintenance_email = models.BooleanField(default=True, verbose_name="Maintenance système - Email")
    system_maintenance_push = models.BooleanField(default=True, verbose_name="Maintenance système - Push")
    system_maintenance_in_app = models.BooleanField(default=True, verbose_name="Maintenance système - In-App")

    # Paramètres globaux
    email_notifications_enabled = models.BooleanField(default=True, verbose_name="Notifications email activées")
    push_notifications_enabled = models.BooleanField(default=True, verbose_name="Notifications push activées")
    in_app_notifications_enabled = models.BooleanField(default=True, verbose_name="Notifications in-app activées")

    # Fréquence des emails de synthèse (en heures, 0 pour désactivé)
    digest_frequency = models.IntegerField(
        default=24,
        choices=[(0, 'Jamais'), (6, 'Toutes les 6 heures'), (12, 'Toutes les 12 heures'),
                 (24, 'Quotidien'), (168, 'Hebdomadaire')],
        verbose_name="Fréquence des emails de synthèse"
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'xcsm_notification_preference'
        verbose_name = 'Préférence de notification'
        verbose_name_plural = 'Préférences de notification'

    def __str__(self):
        return f"Préférences de {self.utilisateur.username}"

    def get_preference_for_type(self, notification_type, channel):
        """
        Récupère la préférence pour un type de notification et un canal donné.

        Args:
            notification_type (str): Type de notification (ex: 'DOCUMENT_TRAITE')
            channel (str): Canal ('email', 'push', 'in_app')

        Returns:
            bool: True si l'utilisateur accepte cette notification, False sinon
        """
        # Mapper le type de notification au champ correspondant
        field_map = {
            'DOCUMENT_TRAITE': f'document_traite_{channel}',
            'DOCUMENT_ERREUR': f'document_erreur_{channel}',
            'NOUVELLE_EVALUATION': f'nouvelle_evaluation_{channel}',
            'EVALUATION_CORRIGEE': f'evaluation_corrigee_{channel}',
            'NOUVEAU_MESSAGE': f'nouveau_message_{channel}',
            'SYSTEM_MAINTENANCE': f'system_maintenance_{channel}',
        }

        field_name = field_map.get(notification_type)
        if not field_name:
            # Type de notification non géré, on retourne False par défaut
            return False

        # Vérifier si le canal est activé globalement
        channel_enabled_field = f'{channel}_notifications_enabled'
        if not getattr(self, channel_enabled_field, True):
            return False

        # Retourner la préférence spécifique
        return getattr(self, field_name, False)


class Notification(models.Model):
    """
    Notification envoyée à un utilisateur.
    Une notification peut être envoyée via plusieurs canaux (in-app, email, push).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Type de notification
    TYPE_CHOICES = [
        ('DOCUMENT_TRAITE', 'Document traité'),
        ('DOCUMENT_ERREUR', 'Erreur de traitement'),
        ('NOUVELLE_EVALUATION', 'Nouvelle évaluation'),
        ('EVALUATION_CORRIGEE', 'Évaluation corrigée'),
        ('NOUVEAU_MESSAGE', 'Nouveau message'),
        ('SYSTEM_MAINTENANCE', 'Maintenance système'),
        ('PROFIL_MIS_A_JOUR', 'Profil mis à jour'),
        ('AUTRE', 'Autre'),
    ]

    type_notification = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name="Type de notification"
    )

    # Contenu de la notification
    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")

    # Données supplémentaires (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires au format JSON (ex: IDs des objets concernés)"
    )

    # État de la notification
    EST_VUE_CHOICES = [
        ('NON_VUE', 'Non vue'),
        ('VUE', 'Vue'),
        ('ARCHIVEE', 'Archivée'),
    ]
    est_vue = models.CharField(
        max_length=20,
        choices=EST_VUE_CHOICES,
        default='NON_VUE',
        verbose_name="État"
    )

    # Canaux utilisés pour l'envoi
    envoyee_email = models.BooleanField(default=False, verbose_name="Envoyée par email")
    envoyee_push = models.BooleanField(default=False, verbose_name="Envoyée par push")
    envoyee_in_app = models.BooleanField(default=True, verbose_name="Disponible in-app")

    # Références aux objets concernés (optionnel)
    fichier_source = models.ForeignKey(
        FichierSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    granule = models.ForeignKey(
        Granule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_envoi = models.DateTimeField(null=True, blank=True, verbose_name="Date d'envoi")
    date_lecture = models.DateTimeField(null=True, blank=True, verbose_name="Date de lecture")
    date_archivage = models.DateTimeField(null=True, blank=True, verbose_name="Date d'archivage")

    # Pour les emails
    email_message_id = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="ID du message email"
    )
    email_statut = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[('ENVOYE', 'Envoyé'), ('ECHEC', 'Échec'), ('OUVERT', 'Ouvert'), ('CLIQUE', 'Cliqué')],
        verbose_name="Statut email"
    )

    # Pour les push
    push_message_id = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="ID du message push"
    )
    push_statut = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[('ENVOYE', 'Envoyé'), ('RECU', 'Reçu'), ('OUVERT', 'Ouvert'), ('ECHEC', 'Échec')],
        verbose_name="Statut push"
    )

    class Meta:
        db_table = 'xcsm_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'est_vue', 'date_creation']),
            models.Index(fields=['type_notification', 'date_creation']),
            models.Index(fields=['fichier_source']),
            models.Index(fields=['cours']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username}"

    def marquer_comme_vue(self):
        """
        Marque la notification comme vue.
        """
        if self.est_vue == 'NON_VUE':
            self.est_vue = 'VUE'
            self.date_lecture = timezone.now()
            self.save(update_fields=['est_vue', 'date_lecture'])

    def archiver(self):
        """
        Archive la notification.
        """
        self.est_vue = 'ARCHIVEE'
        self.date_archivage = timezone.now()
        self.save(update_fields=['est_vue', 'date_archivage'])

    def get_metadata_value(self, key, default=None):
        """
        Récupère une valeur spécifique des métadonnées.

        Args:
            key (str): Clé à récupérer
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            La valeur correspondante ou la valeur par défaut
        """
        return self.metadata.get(key, default)


class PushSubscription(models.Model):
    """
    Abonnement aux notifications push (pour web et mobile).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )

    # Type de device
    DEVICE_TYPES = [
        ('WEB', 'Navigateur web'),
        ('ANDROID', 'Android'),
        ('IOS', 'iOS'),
        ('OTHER', 'Autre'),
    ]
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        verbose_name="Type d'appareil"
    )

    # Informations sur l'appareil
    device_id = models.CharField(
        max_length=500,
        unique=True,
        verbose_name="ID de l'appareil",
        help_text="Identifiant unique de l'appareil"
    )
    device_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Nom de l'appareil"
    )
    device_model = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Modèle de l'appareil"
    )

    # Données d'abonnement
    subscription_data = models.JSONField(
        verbose_name="Données d'abonnement",
        help_text="Données d'abonnement au format spécifique au device"
    )

    # Clés pour Web Push (VAPID)
    vapid_public_key = models.TextField(
        null=True,
        blank=True,
        verbose_name="Clé publique VAPID"
    )
    vapid_private_key = models.TextField(
        null=True,
        blank=True,
        verbose_name="Clé privée VAPID"
    )

    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Dernière connexion")

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_desactivation = models.DateTimeField(null=True, blank=True, verbose_name="Date de désactivation")

    class Meta:
        db_table = 'xcsm_push_subscription'
        verbose_name = 'Abonnement push'
        verbose_name_plural = 'Abonnements push'
        unique_together = ['utilisateur', 'device_id']
        indexes = [
            models.Index(fields=['utilisateur', 'is_active']),
            models.Index(fields=['device_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.device_type} - {self.utilisateur.username}"

    def desactiver(self):
        """
        Désactive l'abonnement push.
        """
        self.is_active = False
        self.date_desactivation = timezone.now()
        self.save(update_fields=['is_active', 'date_desactivation'])


class NotificationDigest(models.Model):
    """
    Email de synthèse des notifications.
    Regroupe plusieurs notifications pour les envoyer en un seul email.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notification_digests'
    )

    # Contenu
    notifications = models.ManyToManyField(
        Notification,
        related_name='digests',
        verbose_name="Notifications incluses"
    )
    contenu_html = models.TextField(verbose_name="Contenu HTML")
    contenu_text = models.TextField(verbose_name="Contenu texte")

    # Statut d'envoi
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ENVOYE', 'Envoyé'),
        ('ECHEC', 'Échec'),
        ('OUVERT', 'Ouvert'),
    ]
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name="Statut"
    )

    # Suivi email
    email_message_id = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="ID du message email"
    )
    email_ouvert = models.BooleanField(default=False, verbose_name="Email ouvert")
    email_clique = models.BooleanField(default=False, verbose_name="Email cliqué")

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_envoi = models.DateTimeField(null=True, blank=True, verbose_name="Date d'envoi")
    date_ouverture = models.DateTimeField(null=True, blank=True, verbose_name="Date d'ouverture")
    date_clic = models.DateTimeField(null=True, blank=True, verbose_name="Date de clic")

    class Meta:
        db_table = 'xcsm_notification_digest'
        verbose_name = 'Synthèse de notifications'
        verbose_name_plural = 'Synthèses de notifications'
        ordering = ['-date_creation']

    def __str__(self):
        return f"Synthèse pour {self.utilisateur.username} - {self.date_creation.strftime('%Y-%m-%d %H:%M')}"

    def marquer_comme_envoye(self, email_message_id=None):
        """
        Marque la synthèse comme envoyée.

        Args:
            email_message_id (str, optional): ID du message email
        """
        self.statut = 'ENVOYE'
        self.date_envoi = timezone.now()
        if email_message_id:
            self.email_message_id = email_message_id
        self.save(update_fields=['statut', 'date_envoi', 'email_message_id'])

    def marquer_comme_ouvert(self):
        """
        Marque la synthèse comme ouverte.
        """
        if not self.email_ouvert:
            self.email_ouvert = True
            self.date_ouverture = timezone.now()
            self.save(update_fields=['email_ouvert', 'date_ouverture'])

    def marquer_comme_clique(self):
        """
        Marque la synthèse comme cliquée.
        """
        if not self.email_clique:
            self.email_clique = True
            self.date_clic = timezone.now()
            self.save(update_fields=['email_clique', 'date_clic'])


class NotificationTemplate(models.Model):
    """
    Template pour les notifications.
    Permet de gérer les messages de manière centralisée.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identifiant du template
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Code du template"
    )
    nom = models.CharField(max_length=200, verbose_name="Nom")

    # Type de notification
    type_notification = models.CharField(
        max_length=50,
        choices=Notification.TYPE_CHOICES,
        verbose_name="Type de notification"
    )

    # Templates par canal
    template_email_sujet = models.CharField(
        max_length=200,
        verbose_name="Sujet email"
    )
    template_email_html = models.TextField(verbose_name="Template email HTML")
    template_email_text = models.TextField(verbose_name="Template email texte")

    template_push_titre = models.CharField(
        max_length=100,
        verbose_name="Titre push"
    )
    template_push_message = models.TextField(verbose_name="Message push")

    template_in_app_titre = models.CharField(
        max_length=100,
        verbose_name="Titre in-app"
    )
    template_in_app_message = models.TextField(verbose_name="Message in-app")

    # Variables disponibles dans le template
    variables_disponibles = models.JSONField(
        default=list,
        verbose_name="Variables disponibles",
        help_text="Liste des variables disponibles dans le template"
    )

    # Activation
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")

    class Meta:
        db_table = 'xcsm_notification_template'
        verbose_name = 'Template de notification'
        verbose_name_plural = 'Templates de notification'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.nom}"

    def render_email(self, context):
        """
        Rendu du template email avec le contexte fourni.

        Args:
            context (dict): Contexte pour le rendu

        Returns:
            tuple: (sujet, html, texte)
        """
        # Implémentation basique - à compléter avec un moteur de template
        sujet = self.template_email_sujet
        html = self.template_email_html
        texte = self.template_email_text

        # Remplacement simple des variables
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            sujet = sujet.replace(placeholder, str(value))
            html = html.replace(placeholder, str(value))
            texte = texte.replace(placeholder, str(value))

        return sujet, html, texte

    def render_push(self, context):
        """
        Rendu du template push avec le contexte fourni.

        Args:
            context (dict): Contexte pour le rendu

        Returns:
            tuple: (titre, message)
        """
        titre = self.template_push_titre
        message = self.template_push_message

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            titre = titre.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))

        return titre, message

    def render_in_app(self, context):
        """
        Rendu du template in-app avec le contexte fourni.

        Args:
            context (dict): Contexte pour le rendu

        Returns:
            tuple: (titre, message)
        """
        titre = self.template_in_app_titre
        message = self.template_in_app_message

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            titre = titre.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))

        return titre, message