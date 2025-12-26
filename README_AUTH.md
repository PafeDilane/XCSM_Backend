# Authentification JWT - Documentation Technique

## Vue d'ensemble
Implémentation d'un système d'authentification JWT sécurisé pour l'API XCSM. Cette authentification permet aux utilisateurs (enseignants, étudiants, administrateurs) de s'authentifier et d'accéder aux ressources protégées de la plateforme.

## Endpoints JWT

### 1. Inscription Utilisateur
```
POST /api/v1/auth/register/
```
**Corps de la requête :**
```json
{
  "username": "jean.martin",
  "email": "jean.martin@gmail.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "type_compte": "ENSEIGNANT",
  "first_name": "Jean",
  "last_name": "Martin",
  "telephone": "+237 6 99 88 77 66",
  "ville": "Yaoundé",
  "pays": "Cameroun"
}
```

**Réponse réussie (201) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "jean.martin",
    "email": "jean.martin@gmail.com",
    "type_compte": "ENSEIGNANT"
  }
}
```

### 2. Connexion Utilisateur
```
POST /api/v1/auth/login/
```
**Corps de la requête :**
```json
{
  "username": "jean.martin",
  "password": "SecurePass123!"
}
```

**Réponse réussie (200) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Rafraîchissement du Token d'Accès
```
POST /api/v1/auth/refresh/
```
**Corps de la requête :**
```json
{
  "refresh": "votre_refresh_token_ici"
}
```

**Réponse réussie (200) :**
```json
{
  "access": "nouveau_token_d_acces"
}
```

### 4. Profil Utilisateur
```
GET /api/v1/auth/profile/
```
**En-têtes :**
```
Authorization: Bearer votre_token_d_acces
```

**Réponse réussie (200) :**
```json
{
  "id": 1,
  "username": "jean.martin",
  "email": "jean.martin@gmail.com",
  "first_name": "Jean",
  "last_name": "Martin",
  "type_compte": "ENSEIGNANT",
  "telephone": "+237 6 99 88 77 66",
  "ville": "Yaoundé",
  "pays": "Cameroun",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

```
PUT /api/v1/auth/profile/
```
**Corps de la requête :**
```json
{
  "first_name": "Jean-Pierre",
  "telephone": "+237 6 77 66 55 44"
}
```

### 5. Changement de Mot de Passe
```
PUT /api/v1/auth/change-password/
```
**Corps de la requête :**
```json
{
  "old_password": "ancien_mot_de_passe",
  "new_password": "nouveau_mot_de_passe"
}
```

### 6. Déconnexion
```
POST /api/v1/auth/logout/
```
**Corps de la requête :**
```json
{
  "refresh": "votre_refresh_token_ici"
}
```

## Tests d'Authentification

### Exécution des Tests
```bash
# Exécuter tous les tests d'authentification
python scripts/test_jwt_auth.py

# Sortie attendue :
# ============================================
# SUITE DE TESTS JWT - XCSM PROJECT
# ============================================
# [PASS] Connexion au serveur
# [PASS] Inscription utilisateur
# [PASS] Connexion utilisateur
# [PASS] Rafraîchissement token
# [PASS] Accès endpoint protégé
# [PASS] Upload avec authentification
# [PASS] Déconnexion
# ============================================
# RESULTAT: 7/7 tests réussis
# SUCCES: Tous les tests sont valides
```

### Configuration des Tests
Les tests utilisent un utilisateur de test avec les caractéristiques suivantes :
- **Nom d'utilisateur** : test.enseignant
- **Email** : test.enseignant@gmail.com (format standard pour le Cameroun)
- **Téléphone** : Format local +237
- **Localisation** : Informations pertinentes pour le contexte

## Sécurité

### Mesures de Sécurité Implémentées
1. **Tokens JWT avec expiration**
    - Token d'accès : 15 minutes
    - Token de rafraîchissement : 7 jours

2. **Gestion sécurisée des tokens**
    - Refresh tokens rotatifs
    - Blacklist pour déconnexion contrôlée
    - Validation cryptographique des signatures

3. **Protection des mots de passe**
    - Hash avec bcrypt
    - Validation de complexité
    - Protection contre les attaques par force brute

4. **Rate Limiting**
    - Limitation des tentatives de connexion
    - Protection contre les attaques DDoS

### Bonnes Pratiques pour les Clients

#### Headers d'Authentification
```javascript
// Exemple avec JavaScript/Fetch
fetch('/api/v1/auth/profile/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer votre_token_d_acces',
    'Content-Type': 'application/json'
  }
});
```

#### Gestion des Tokens
```javascript
// Stockage sécurisé des tokens
localStorage.setItem('access_token', response.access);
localStorage.setItem('refresh_token', response.refresh);

// Rafraîchissement automatique du token
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/api/v1/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });
  // Mettre à jour le token d'accès
}
```

## Intégration avec l'Écosystème XCSM

### Types de Compte Supportés
- **ENSEIGNANT** : Accès complet aux fonctionnalités pédagogiques
- **ETUDIANT** : Accès aux ressources d'apprentissage
- **ADMINISTRATEUR** : Gestion complète de la plateforme

### Workflow Typique
1. Inscription avec informations personnelles
2. Connexion pour obtenir les tokens JWT
3. Utilisation du token d'accès pour les requêtes API
4. Rafraîchissement automatique lorsque nécessaire
5. Déconnexion pour invalider les tokens

## Résolution des Problèmes Courants

### Problèmes de Connexion
| Symptôme | Cause Possible | Solution |
|----------|---------------|----------|
| 401 Unauthorized | Token expiré | Rafraîchir le token |
| 400 Bad Request | Données invalides | Vérifier le format JSON |
| 403 Forbidden | Permissions insuffisantes | Vérifier le type de compte |

### Gestion des Erreurs
```json
{
  "error": "invalid_credentials",
  "message": "Nom d'utilisateur ou mot de passe incorrect"
}
```

## Commandes Git pour le Développement

```bash
# Créer et basculer sur la branche d'authentification
git checkout -b feature/auth-jwt-implementation

# Ajouter les modifications
git add .
git commit -m "feat: implémentation complète du système d'authentification JWT
- Ajout des endpoints d'inscription, connexion et rafraîchissement
- Implémentation de la sécurité avec tokens JWT
- Tests complets d'authentification
- Documentation technique détaillée"

# Pousser la branche vers le dépôt distant
git push origin feature/auth-jwt-implementation

# Créer une Pull Request pour fusion dans main
# (À faire via l'interface GitHub/GitLab)

# Revenir à la branche principale après fusion
git checkout main
git pull origin main
```

## Support et Maintenance

Pour tout problème lié à l'authentification :
1. Vérifier la validité des tokens
2. Confirmer les permissions utilisateur
3. Consulter les logs d'application
4. Contacter l'équipe technique si nécessaire

---

*Documentation mise à jour : Decembre 2025  
Team XCSM 4GI ENSPY Promo 2027- Système de Gestion de Contenus Pédagogiques*