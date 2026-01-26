from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import ActionLog, FichierSource, Cours, Evaluation, Correction

import logging
logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    try:
        metadata = {}
        if request:
            metadata['ip'] = request.META.get('REMOTE_ADDR')
            
        ActionLog.objects.create(
            utilisateur=user,
            action_type='LOGIN',
            description=f"Utilisateur {user.username} s'est connecté.",
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"⚠️ Erreur lors du log du login : {e}")

@receiver(post_save, sender=FichierSource)
def log_document_upload_or_modify(sender, instance, created, **kwargs):
    try:
        action = 'UPLOAD' if created else 'MODIFY'
        desc = f"Document '{instance.titre}' uploadé." if created else f"Document '{instance.titre}' modifié."
        ActionLog.objects.create(
            utilisateur=instance.enseignant.utilisateur,
            action_type=action,
            description=desc,
            metadata={'document_id': str(instance.id)}
        )
    except Exception as e:
        logger.error(f"⚠️ Erreur lors du log du document upload : {e}")

@receiver(post_save, sender=Cours)
def log_cours_save(sender, instance, created, **kwargs):
    try:
        action = 'PUBLISH' if (not created and instance.est_publie) else 'MODIFY'
        if created: action = 'MODIFY' # Draft creation
        desc = f"Cours '{instance.titre}' créé/modifié."
        if not created and instance.est_publie:
            desc = f"Cours '{instance.titre}' publié."
        
        ActionLog.objects.create(
            utilisateur=instance.enseignant.utilisateur,
            action_type=action,
            description=desc,
            metadata={'cours_id': str(instance.id), 'code': instance.code}
        )
    except Exception as e:
        logger.error(f"⚠️ Erreur lors du log de sauvegarde du cours : {e}")

@receiver(post_delete, sender=FichierSource)
def log_document_delete(sender, instance, **kwargs):
    try:
        ActionLog.objects.create(
            utilisateur=instance.enseignant.utilisateur,
            action_type='DELETE',
            description=f"Document '{instance.titre}' supprimé.",
            metadata={'document_id': str(instance.id)}
        )
    except Exception as e:
        logger.error(f"⚠️ Erreur lors du log de suppression du document : {e}")
