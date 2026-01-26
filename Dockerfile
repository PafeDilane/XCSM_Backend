# Utilisation d'une image Python légère et stable
FROM python:3.12-slim

# Empêcher Python de générer des fichiers .pyc et forcer l'affichage des logs en temps réel
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définition du répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires (MySQL client, build essentials, libmagic, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Rendre l'entrypoint exécutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exposition du port Django
EXPOSE 8000

# Utilisation de l'entrypoint pour gérer les migrations au démarrage
ENTRYPOINT ["/entrypoint.sh"]
