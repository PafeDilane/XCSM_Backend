# xcsm/serializers.py
from rest_framework import serializers
from .models import FichierSource

class FichierSourceSerializer(serializers.ModelSerializer):
    
    """ Sérialiseur pour la classe FichierSource (Upload) """
    class Meta:
        model = FichierSource
        # Le frontend nous envoie le titre et le fichier
        fields = ['titre', 'fichier_original']
        read_only_fields = ['enseignant', 'statut_traitement', 'type_mime', 'mongo_transforme_id']