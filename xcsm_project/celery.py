import os
from celery import Celery

# Définir le module de paramètres Django par défaut pour le programme 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xcsm_project.settings')

app = Celery('xcsm_project')

# Utiliser une chaîne ici signifie que le worker n'a pas besoin de sérialiser
# l'objet de configuration pour les processus enfants.
# - namespace='CELERY' signifie que toutes les clés de configuration liées à celery
#   doivent avoir le préfixe `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger les modules de tâches de toutes les applications Django enregistrées.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
