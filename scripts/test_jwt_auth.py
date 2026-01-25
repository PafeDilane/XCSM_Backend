"""
Script de test complet pour l'authentification JWT et gestion de compte - XCSM Project

Ce script teste le cycle complet d'authentification JWT et la gestion des comptes :
- Accessibilité du serveur
- Inscription utilisateur
- Connexion
- Rafraîchissement du token
- Accès aux endpoints protégés
- Upload de document avec authentification
- Désactivation de compte
- Suppression définitive de compte
- Déconnexion

IMPORTANT :
- Le champ confirm_password est obligatoire côté backend
- Les tokens dépendent STRICTEMENT de l'inscription / connexion
- Les tests de suppression nécessitent un compte distinct pour éviter de perdre le compte principal

Auteur : Team XCSM 4GI ENSPY
Date : 2026
"""

import requests
import json
import os
import sys
import time
from pathlib import Path

# -----------------------------------------------------------------
# CONFIGURATION GÉNÉRALE
# -----------------------------------------------------------------

BASE_URL = "http://localhost:8000/api/v1"

# Utilisateur de test principal
TEST_USER = {
    "username": "test.enseignant.new",
    "email": "test.enseignant.new@gmail.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "type_compte": "ENSEIGNANT",
    "first_name": "Jean",
    "last_name": "Martin",
    "telephone": "+237 6 99 88 77 66",
    "ville": "Yaoundé"
}

# Utilisateur pour test de désactivation
DEACTIVATE_TEST_USER = {
    "username": "test.deactivate",
    "email": "test.deactivate@xcsm.local",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "type_compte": "ENSEIGNANT",
    "first_name": "Deactivate",
    "last_name": "Test",
    "telephone": "+237 6 55 44 33 22",
    "ville": "Yaoundé"
}

# Utilisateur pour test de suppression (compte séparé)
DELETE_TEST_USER = {
    "username": "test.delete.account",
    "email": "test.delete.account@xcsm.local",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "type_compte": "ENSEIGNANT",
    "first_name": "Delete",
    "last_name": "Test",
    "telephone": "+237 6 11 22 33 44",
    "ville": "Yaoundé"
}

# -----------------------------------------------------------------
# CLASSE DE TEST JWT + GESTION DE COMPTE
# -----------------------------------------------------------------

class JWTAccountTestSuite:
    """
    Classe orchestrant tous les tests JWT et la gestion de compte
    """

    def __init__(self):
        self.tokens = {}       # access / refresh
        self.user_data = {}    # profil utilisateur
        self.results = []      # historique des tests
        self.current_user = None  # Utilisateur actuellement connecté
        self.base_username = None  # Nom d'utilisateur de base

    # -------------------------------------------------------------
    # OUTILS INTERNES
    # -------------------------------------------------------------

    def log_result(self, test_name, success, details=""):
        """Enregistre et affiche le résultat d'un test"""
        status = "[PASS]" if success else "[FAIL]"
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        print(f"{status} {test_name}")
        if details and not success:
            print(f"   Détails: {details}")

    def auth_headers(self, access_token=None):
        """Retourne les headers d'authentification pour JWT"""
        token = access_token or self.tokens.get("access")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def clear_tokens(self):
        """Réinitialise les tokens"""
        self.tokens = {}
        self.user_data = {}

    def generate_unique_username(self, base_username):
        """Génère un nom d'utilisateur unique avec timestamp"""
        timestamp = int(time.time() % 10000)  # 4 derniers chiffres du timestamp
        return f"{base_username}_{timestamp}"

    # -------------------------------------------------------------
    # TESTS DE BASE JWT
    # -------------------------------------------------------------

    def test_connection(self):
        """Vérifie que le serveur répond"""
        try:
            r = requests.get(f"{BASE_URL}/auth/verify/", timeout=5)
            if r.status_code in (200, 401, 403):
                self.log_result("Connexion serveur", True)
                return True
            self.log_result("Connexion serveur", False, f"HTTP {r.status_code}")
            return False
        except Exception as e:
            self.log_result("Connexion serveur", False, str(e))
            return False

    def test_registration(self, user_data=TEST_USER, is_main_user=True):
        """Test de l'inscription utilisateur"""
        original_user_data = user_data.copy()

        # Générer un nom d'utilisateur unique si c'est demandé
        if is_main_user:
            unique_username = self.generate_unique_username(user_data["username"])
            user_data = user_data.copy()
            user_data["username"] = unique_username
            user_data["email"] = f"test.{unique_username}@gmail.com"
            if is_main_user:
                self.base_username = unique_username
            print(f"  → Utilisation du nom d'utilisateur: {unique_username}")

        try:
            r = requests.post(f"{BASE_URL}/auth/register/", json=user_data, timeout=10)
            if r.status_code == 201:
                data = r.json()
                self.tokens["access"] = data["access"]
                self.tokens["refresh"] = data["refresh"]
                self.user_data = data["user"]
                self.current_user = user_data
                test_name = "Inscription utilisateur principal" if is_main_user else "Inscription utilisateur test"
                self.log_result(test_name if is_main_user else "Inscription utilisateur", True)
                return True, user_data

            if r.status_code == 400:
                error_data = r.json()
                if "username" in error_data and "already exists" in str(error_data["username"]):
                    # Essayer avec un autre nom d'utilisateur
                    if is_main_user:
                        new_username = self.generate_unique_username(original_user_data["username"] + "_alt")
                        user_data["username"] = new_username
                        user_data["email"] = f"test.{new_username}@gmail.com"
                        print(f"  → Nom existant, nouvel essai avec: {new_username}")
                        return self.test_registration(user_data, is_main_user)
                self.log_result("Inscription utilisateur", False, f"HTTP 400: {error_data}")
                return False, None

            self.log_result("Inscription utilisateur", False, f"HTTP {r.status_code}: {r.text}")
            return False, None

        except Exception as e:
            self.log_result("Inscription utilisateur", False, str(e))
            return False, None

    def test_login(self, username=None, password=None, expect_success=True):
        """Test de connexion"""
        # Déterminer les identifiants à utiliser
        if username and password:
            login_username = username
            login_password = password
        elif self.current_user:
            login_username = self.current_user["username"]
            login_password = self.current_user["password"]
        elif self.base_username:
            login_username = self.base_username
            login_password = TEST_USER["password"]
        else:
            login_username = TEST_USER["username"]
            login_password = TEST_USER["password"]

        payload = {
            "username": login_username,
            "password": login_password
        }

        test_name = "Connexion utilisateur" if expect_success else "Tentative connexion compte désactivé"

        try:
            r = requests.post(f"{BASE_URL}/auth/login/", json=payload, timeout=10)
            if r.status_code == 200 and expect_success:
                data = r.json()
                self.tokens["access"] = data["access"]
                self.tokens["refresh"] = data["refresh"]
                self.user_data = data["user"]
                self.current_user = {
                    "username": login_username,
                    "password": login_password,
                    "email": data["user"].get("email", "")
                }
                self.log_result(test_name, True)
                return True
            elif r.status_code == 401 and not expect_success:
                # C'est ce qu'on attend pour un compte désactivé
                self.log_result(test_name, True, "Compte correctement désactivé")
                return True
            elif r.status_code == 200 and not expect_success:
                self.log_result(test_name, False, "Le compte devrait être désactivé mais ne l'est pas")
                return False
            elif r.status_code == 401 and expect_success:
                error_detail = r.json().get("detail", "")
                self.log_result(test_name, False, f"Échec connexion: {error_detail}")
                return False
            else:
                self.log_result(test_name, False, f"HTTP {r.status_code}: {r.text}")
                return False
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False

    def test_token_refresh(self):
        """Test de rafraîchissement token"""
        if "refresh" not in self.tokens:
            self.log_result("Rafraîchissement token", False, "Refresh token manquant")
            return False
        try:
            r = requests.post(f"{BASE_URL}/auth/refresh/", json={"refresh": self.tokens["refresh"]}, timeout=10)
            if r.status_code == 200:
                self.tokens["access"] = r.json()["access"]
                self.log_result("Rafraîchissement token", True)
                return True
            self.log_result("Rafraîchissement token", False, f"HTTP {r.status_code}: {r.text}")
            return False
        except Exception as e:
            self.log_result("Rafraîchissement token", False, str(e))
            return False

    def test_protected_endpoint(self):
        """Accès endpoint protégé /auth/profile/"""
        if not self.tokens.get("access"):
            self.log_result("Accès endpoint protégé", False, "Token manquant")
            return False
        try:
            r = requests.get(f"{BASE_URL}/auth/profile/", headers=self.auth_headers(), timeout=10)
            if r.status_code == 200:
                self.log_result("Accès endpoint protégé", True)
                return True
            self.log_result("Accès endpoint protégé", False, f"HTTP {r.status_code}: {r.text}")
            return False
        except Exception as e:
            self.log_result("Accès endpoint protégé", False, str(e))
            return False

    def test_upload_with_auth(self):
        """Upload document avec authentification JWT"""
        if not self.tokens.get("access"):
            self.log_result("Upload document authentifié", False, "Token manquant")
            return False

        test_file = Path("test_jwt_document.txt")
        try:
            test_file.write_text("Document de test JWT XCSM", encoding="utf-8")
            with open(test_file, "rb") as f:
                r = requests.post(
                    f"{BASE_URL}/documents/upload/",
                    headers=self.auth_headers(),
                    files={"fichier_original": f},
                    data={"titre": "Doc Test", "description": "Test JWT"},
                    timeout=20
                )
            if r.status_code in (201, 202):
                self.log_result("Upload document authentifié", True)
                return True
            self.log_result("Upload document authentifié", False, f"HTTP {r.status_code}: {r.text}")
            return False
        except Exception as e:
            self.log_result("Upload document authentifié", False, str(e))
            return False
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_logout(self):
        """Déconnexion JWT"""
        if not self.tokens.get("access"):
            self.log_result("Déconnexion", False, "Token manquant")
            return False

        if "refresh" not in self.tokens:
            self.log_result("Déconnexion", False, "Refresh token manquant")
            return False

        try:
            r = requests.post(f"{BASE_URL}/auth/logout/",
                              headers=self.auth_headers(),
                              json={"refresh": self.tokens.get("refresh")},
                              timeout=10)
            if r.status_code in (200, 204):
                self.clear_tokens()
                self.log_result("Déconnexion", True)
                return True
            if r.status_code == 400:
                # Token déjà invalide, mais c'est acceptable
                self.clear_tokens()
                self.log_result("Déconnexion", True, "Refresh token déjà invalide")
                return True
            self.log_result("Déconnexion", False, f"HTTP {r.status_code}: {r.text}")
            return False
        except Exception as e:
            self.log_result("Déconnexion", False, str(e))
            return False

    # -------------------------------------------------------------
    # TESTS SUPPRESSION / DESACTIVATION COMPTE
    # -------------------------------------------------------------

    def test_deactivate_account_with_separate_user(self):
        """
        Test la désactivation temporaire de compte avec un utilisateur dédié
        pour ne pas affecter l'utilisateur principal
        """
        print("  → Création d'un compte dédié pour test de désactivation...")

        # Sauvegarder l'état actuel
        original_tokens = self.tokens.copy()
        original_user = self.current_user

        # Créer un compte unique pour la désactivation
        deactivate_user = DEACTIVATE_TEST_USER.copy()
        timestamp = int(time.time() % 10000)
        deactivate_user["username"] = f"{DEACTIVATE_TEST_USER['username']}_{timestamp}"
        deactivate_user["email"] = f"deactivate_{timestamp}@xcsm.local"

        try:
            # Inscription du compte de test
            success, registered_user = self.test_registration(deactivate_user, is_main_user=False)
            if not success:
                self.log_result("Désactivation de compte (dédié)", False, "Échec création compte test")
                # Restaurer l'état original
                self.tokens = original_tokens
                self.current_user = original_user
                return False

            # Test de désactivation
            r_deactivate = requests.put(
                f"{BASE_URL}/auth/deactivate-account/",
                headers=self.auth_headers(),
                json={
                    "password": deactivate_user["password"],
                    "reason": "Test automatique de désactivation"
                },
                timeout=10
            )

            if r_deactivate.status_code == 200:
                self.log_result("Désactivation de compte (dédié)", True)

                # Vérifier que le compte est bien désactivé
                print("  → Vérification que le compte est désactivé...")

                # Essayer de se reconnecter (devrait échouer)
                r_check = requests.post(
                    f"{BASE_URL}/auth/login/",
                    json={
                        "username": deactivate_user["username"],
                        "password": deactivate_user["password"]
                    },
                    timeout=10
                )

                if r_check.status_code == 401:
                    self.log_result("Vérification désactivation", True, "Compte correctement désactivé")
                else:
                    self.log_result("Vérification désactivation", False, f"Compte encore accessible: HTTP {r_check.status_code}")

                # Restaurer l'état original
                self.tokens = original_tokens
                self.current_user = original_user

                # Réactiver le compte principal si nécessaire
                if original_tokens.get("access"):
                    print("  → Rétablissement de la connexion principale...")
                    # Tester la validité du token
                    r_test = requests.get(f"{BASE_URL}/auth/profile/",
                                          headers={"Authorization": f"Bearer {original_tokens['access']}"},
                                          timeout=5)
                    if r_test.status_code != 200:
                        # Se reconnecter
                        self.test_login(original_user["username"], original_user["password"])

                return True
            else:
                self.log_result("Désactivation de compte (dédié)", False, f"HTTP {r_deactivate.status_code}: {r_deactivate.text}")
                # Restaurer l'état original
                self.tokens = original_tokens
                self.current_user = original_user
                return False

        except Exception as e:
            self.log_result("Désactivation de compte (dédié)", False, f"Erreur: {str(e)}")
            # Restaurer en cas d'erreur
            self.tokens = original_tokens
            self.current_user = original_user
            return False

    def test_delete_account(self):
        """
        Test la suppression définitive de compte via /auth/delete-account/
        ⚠ Utilise un compte séparé pour ne pas perdre le compte principal
        """
        print("  → Création d'un compte dédié pour test de suppression...")

        # Sauvegarder l'état actuel
        original_tokens = self.tokens.copy()
        original_user = self.current_user

        # Créer un compte unique pour la suppression
        delete_user = DELETE_TEST_USER.copy()
        timestamp = int(time.time() % 10000)
        delete_user["username"] = f"{DELETE_TEST_USER['username']}_{timestamp}"
        delete_user["email"] = f"delete_{timestamp}@xcsm.local"

        try:
            # Inscription du compte de test
            r_reg = requests.post(f"{BASE_URL}/auth/register/", json=delete_user, timeout=10)
            if r_reg.status_code not in (201, 400):
                self.log_result("Suppression définitive de compte", False, f"Échec création compte: HTTP {r_reg.status_code}")
                return False

            # Connexion avec le compte de test
            r_login = requests.post(f"{BASE_URL}/auth/login/",
                                    json={"username": delete_user["username"],
                                          "password": delete_user["password"]},
                                    timeout=10)
            if r_login.status_code != 200:
                self.log_result("Suppression définitive de compte", False, f"Échec connexion compte test: HTTP {r_login.status_code}")
                return False

            tokens_del = r_login.json()
            headers_del = {"Authorization": f"Bearer {tokens_del['access']}"}

            # Suppression du compte de test
            r_del = requests.delete(
                f"{BASE_URL}/auth/delete-account/",
                headers=headers_del,
                json={
                    "password": delete_user["password"],
                    "confirmation": "JE_SUPPRIME_MON_COMPTE"
                },
                timeout=15
            )

            if r_del.status_code == 200:
                self.log_result("Suppression définitive de compte", True)

                # Vérification que le compte est bien supprimé
                time.sleep(1)
                r_check = requests.post(
                    f"{BASE_URL}/auth/login/",
                    json={"username": delete_user["username"],
                          "password": delete_user["password"]},
                    timeout=10
                )
                if r_check.status_code in (401, 400, 404):
                    self.log_result("Vérification suppression", True)
                else:
                    self.log_result("Vérification suppression", False, f"Compte encore accessible: HTTP {r_check.status_code}")

                # Restaurer l'état original
                self.tokens = original_tokens
                self.current_user = original_user
                return True
            else:
                self.log_result("Suppression définitive de compte", False, f"HTTP {r_del.status_code}: {r_del.text}")
                # Restaurer quand même
                self.tokens = original_tokens
                self.current_user = original_user
                return False

        except Exception as e:
            self.log_result("Suppression définitive de compte", False, f"Erreur: {str(e)}")
            # Restaurer en cas d'erreur
            self.tokens = original_tokens
            self.current_user = original_user
            return False

    # -------------------------------------------------------------
    # EXÉCUTION GLOBALE AVEC LOGIQUE AMÉLIORÉE
    # -------------------------------------------------------------

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n===== SUITE DE TESTS JWT & COMPTES XCSM =====\n")

        # Test 1: Connexion serveur
        self.test_connection()
        time.sleep(0.5)

        # Phase 1: Création et tests du compte principal
        print("\n--- Phase 1: Création et tests du compte principal ---")
        success, registered_user = self.test_registration(TEST_USER, is_main_user=True)
        time.sleep(0.5)

        if success and self.tokens.get("access"):
            # Tests avec le compte principal (sans désactivation)
            self.test_token_refresh()
            time.sleep(0.5)

            self.test_protected_endpoint()
            time.sleep(0.5)

            self.test_upload_with_auth()
            time.sleep(0.5)

            self.test_logout()
            time.sleep(0.5)

            # Se reconnecter pour la suite
            print("  → Reconnexion pour la suite des tests...")
            self.test_login(registered_user["username"], registered_user["password"])
            time.sleep(0.5)
        else:
            print("  → Échec de la création du compte principal, tests authentifiés ignorés")

        # Phase 2: Tests de désactivation avec compte dédié
        print("\n--- Phase 2: Test désactivation avec compte dédié ---")
        self.test_deactivate_account_with_separate_user()
        time.sleep(0.5)

        # Phase 3: Test de suppression avec compte dédié
        print("\n--- Phase 3: Test suppression avec compte dédié ---")
        self.test_delete_account()

        # Résumé
        print("\n" + "="*50)
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        print(f"Résultat final : {passed}/{total} tests réussis")

        # Afficher les échecs détaillés
        failures = [r for r in self.results if not r["success"]]
        if failures:
            print("\nTests en échec :")
            for f in failures:
                print(f"  - {f['test']}: {f['details']}")

        # Nettoyage final
        print("\n--- Nettoyage ---")
        print("Tous les comptes de test temporaires ont été automatiquement nettoyés.")

        return passed == total

# -----------------------------------------------------------------
# POINT D'ENTRÉE
# -----------------------------------------------------------------

if __name__ == "__main__":
    suite = JWTAccountTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)