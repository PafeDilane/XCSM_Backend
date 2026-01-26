#!/bin/bash

# Attendre que MySQL soit prêt (optionnel mais recommandé)
echo "🚀 Démarrage de l'Entrypoint XCSM..."

# Application des migrations MySQL
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecte des fichiers statiques
echo "🎨 Collecte des ressources statiques..."
python manage.py collectstatic --noinput

# Lancement de la commande passée au conteneur (serveur ou worker)
exec "$@"
