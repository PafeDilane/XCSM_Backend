#!/bin/bash

# ==============================================================================
# SCRIPT DE RÉINITIALISATION DE LA DÉMO XCSM
# Réinitialise MySQL, MongoDB et réinjecte le catalogue de Brian Brusly.
# ==============================================================================

echo "🔥 RÉINITIALISATION DE L'ENVIRONNEMENT DE DÉMO..."

# 1. Nettoyage MySQL (Flush des données sans toucher au schéma)
echo "📦 Vidage de la base MySQL..."
./env/bin/python manage.py flush --noinput

# 2. Nettoyage MongoDB
echo "🧠 Vidage de MongoDB..."
./env/bin/python clean_databases.py

# 3. Réinjection des données Brian Brusly
echo "🌟 Création du catalogue de Brian Brusly..."
./env/bin/python generate_extended_test_data.py

# 4. Diagnostic final
echo "🔍 Vérification finale..."
./env/bin/python inspect_data.py

echo "✅ DÉMO PRÊTE ! Vous pouvez lancer le serveur."
