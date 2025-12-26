"""
Script de test complet pour l'authentification JWT - XCSM Project

Ce script teste l'ensemble du système d'authentification JWT du projet XCSM,
y compris l'inscription, la connexion, le rafraîchissement des tokens,
l'accès aux endpoints protégés et les opérations d'upload de documents.

Contexte d'utilisation :
- Test de l'API XCSM dans un environnement de développement local
- Validation du système d'authentification pour les utilisateurs

Exemple d'exécution :
    python test_jwt_auth.py

Auteur : Team XCSM 4gi ENSPY Promo 2027
Date : 2025
"""

import requests
import json
import os
import sys
from pathlib import Path
import time

# -----------------------------------------------------------------
# CONFIGURATION DU TEST
# -----------------------------------------------------------------
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "username": "test.enseignant",
    "email": "test.enseignant@gmail.com",
    "password": "SecurePass123!",
    "type_compte": "ENSEIGNANT",
    "first_name": "Jean",
    "last_name": "Martin",
    "telephone": "+237 6 99 88 77 66",
    "ville": "Yaoundé"
}

# -----------------------------------------------------------------
# CLASSE PRINCIPALE DE TEST
# -----------------------------------------------------------------
class JWTTestSuite:
    """
    Suite de tests pour l'authentification JWT

    Cette classe permet de tester :
    1. La connexion au serveur
    2. L'inscription d'un nouvel utilisateur
    3. La connexion avec identifiants
    4. Le rafraîchissement des tokens JWT
    5. L'accès aux endpoints protégés
    6. L'upload de documents avec authentification
    7. La déconnexion du système
    """

    def __init__(self):
        self.tokens = {}
        self.user_data = {}
        self.results = []

    def log_result(self, test_name, success, details=""):
        """
        Enregistre et affiche le résultat d'un test
        """
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

    def test_connection(self):
        """
        Test la connexion au serveur backend
        """
        try:
            response = requests.get(f"{BASE_URL}/auth/verify/", timeout=5)
            if response.status_code == 200:
                self.log_result("Connexion au serveur", True)
                return True
            else:
                self.log_result("Connexion au serveur", False,
                                f"Code HTTP: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError as e:
            self.log_result("Connexion au serveur", False,
                            f"Impossible de se connecter: {e}")
            return False
        except Exception as e:
            self.log_result("Connexion au serveur", False, str(e))
            return False

    def test_registration(self):
        """
        Test l'inscription d'un nouvel utilisateur
        """
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register/",
                json=TEST_USER,
                timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                self.tokens = {
                    'access': data['access'],
                    'refresh': data['refresh']
                }
                self.user_data = data['user']
                self.log_result("Inscription utilisateur", True)
                return True
            elif response.status_code == 400:
                data = response.json()
                if 'username' in data and 'already exists' in str(data['username']):
                    self.log_result("Inscription utilisateur", True,
                                    "Utilisateur existe déjà (scénario normal)")
                    return True
                else:
                    self.log_result("Inscription utilisateur", False,
                                    f"Erreur 400: {data}")
                    return False
            else:
                self.log_result("Inscription utilisateur", False,
                                f"Code HTTP: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Inscription utilisateur", False, str(e))
            return False

    def test_login(self):
        """
        Test la connexion avec identifiants
        """
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login/",
                json={
                    "username": TEST_USER['username'],
                    "password": TEST_USER['password']
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.tokens = {
                    'access': data['access'],
                    'refresh': data['refresh']
                }
                self.user_data = data['user']
                self.log_result("Connexion utilisateur", True)
                return True
            else:
                self.log_result("Connexion utilisateur", False,
                                f"Code HTTP: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Connexion utilisateur", False, str(e))
            return False

    def test_token_refresh(self):
        """
        Test le rafraîchissement du token d'accès
        """
        try:
            if 'refresh' not in self.tokens:
                self.log_result("Rafraîchissement token", False,
                                "Refresh token non disponible")
                return False

            response = requests.post(
                f"{BASE_URL}/auth/refresh/",
                json={"refresh": self.tokens['refresh']},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.tokens['access'] = data['access']
                self.log_result("Rafraîchissement token", True)
                return True
            else:
                self.log_result("Rafraîchissement token", False,
                                f"Code HTTP: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Rafraîchissement token", False, str(e))
            return False

    def test_protected_endpoint(self):
        """
        Test l'accès à un endpoint protégé
        """
        try:
            if 'access' not in self.tokens:
                self.log_result("Accès endpoint protégé", False,
                                "Access token non disponible")
                return False

            headers = {"Authorization": f"Bearer {self.tokens['access']}"}
            response = requests.get(
                f"{BASE_URL}/auth/profile/",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.log_result("Accès endpoint protégé", True)
                return True
            else:
                self.log_result("Accès endpoint protégé", False,
                                f"Code HTTP: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Accès endpoint protégé", False, str(e))
            return False

    def test_upload_with_auth(self):
        """
        Test l'upload de document avec authentification JWT
        """
        try:
            # Création d'un fichier PDF de test
            test_file = Path("test_jwt_document.pdf")
            if not test_file.exists():
                try:
                    import io
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4

                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=A4)

                    can.setFont("Helvetica", 16)
                    can.drawString(100, 750, "Document de Test - XCSM")

                    can.setFont("Helvetica", 12)
                    can.drawString(100, 720, "Système de Gestion de Contenus Pédagogiques")
                    can.drawString(100, 700, f"Enseignant: {TEST_USER['first_name']} {TEST_USER['last_name']}")
                    can.drawString(100, 680, f"Date: {time.strftime('%d/%m/%Y')}")

                    can.setFont("Helvetica", 10)
                    can.drawString(100, 600, "Ce document est généré automatiquement pour tester")
                    can.drawString(100, 580, "le système d'authentification JWT.")

                    can.save()

                    with open(test_file, "wb") as f:
                        f.write(packet.getvalue())

                    print(f"   Document de test créé: {test_file}")

                except ImportError:
                    # Fallback si reportlab n'est pas installé
                    with open(test_file, 'w') as f:
                        f.write("Contenu de test pour l'authentification JWT\n")
                        f.write(f"Enseignant: {TEST_USER['first_name']} {TEST_USER['last_name']}\n")
                        f.write(f"Email: {TEST_USER['email']}\n")
                        f.write(f"Date: {time.strftime('%Y-%m-%d')}\n")

            # Préparation de la requête d'upload
            if 'access' not in self.tokens:
                self.log_result("Upload avec authentification", False,
                                "Access token non disponible")
                return False

            headers = {"Authorization": f"Bearer {self.tokens['access']}"}

            with open(test_file, 'rb') as file:
                files = {
                    'fichier_original': file
                }
                data = {
                    'titre': 'Document pédagogique de test',
                    'description': 'Document généré automatiquement pour tests',
                    'matiere': 'Informatique',
                    'niveau': 'Licence'
                }

                response = requests.post(
                    f"{BASE_URL}/documents/upload/",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )

            if response.status_code in [201, 202]:
                self.log_result("Upload avec authentification", True)
                return True
            else:
                self.log_result("Upload avec authentification", False,
                                f"Code HTTP: {response.status_code}")
                return False

        except FileNotFoundError as e:
            self.log_result("Upload avec authentification", False,
                            f"Fichier non trouvé: {e}")
            return False
        except Exception as e:
            self.log_result("Upload avec authentification", False, str(e))
            return False

    def test_logout(self):
        """
        Test la déconnexion du système
        """
        try:
            if 'access' not in self.tokens or 'refresh' not in self.tokens:
                self.log_result("Déconnexion", False,
                                "Tokens non disponibles")
                return False

            response = requests.post(
                f"{BASE_URL}/auth/logout/",
                json={"refresh": self.tokens['refresh']},
                headers={"Authorization": f"Bearer {self.tokens['access']}"},
                timeout=10
            )

            if response.status_code == 200:
                self.log_result("Déconnexion", True)
                return True
            else:
                self.log_result("Déconnexion", False,
                                f"Code HTTP: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Déconnexion", False, str(e))
            return False

    def run_all_tests(self):
        """
        Exécute la suite complète des tests
        """
        print("\n" + "="*60)
        print("SUITE DE TESTS JWT - XCSM PROJECT")
        print("="*60)
        print(f"URL de base: {BASE_URL}")
        print(f"Utilisateur test: {TEST_USER['username']}")
        print(f"Début des tests: {time.strftime('%H:%M:%S')}")
        print("-"*60 + "\n")

        # Séquence des tests
        tests = [
            self.test_connection,
            self.test_registration,
            self.test_login,
            self.test_token_refresh,
            self.test_protected_endpoint,
            self.test_upload_with_auth,
            self.test_logout
        ]

        for test in tests:
            test()
            time.sleep(0.5)

        # Génération du rapport
        print("\n" + "-"*60)
        print("RAPPORT DES TESTS")
        print("-"*60)

        successful = sum(1 for r in self.results if r['success'])
        total = len(self.results)

        for result in self.results:
            status = "[PASS]" if result['success'] else "[FAIL]"
            print(f"{status} {result['test']}")

        print("\n" + "="*60)
        print(f"RÉSULTAT: {successful}/{total} tests réussis")

        # Sauvegarde du rapport
        self.save_report()

        if successful == total:
            print("SUCCÈS: Tous les tests sont valides")
            return True
        else:
            print("ATTENTION: Certains tests ont échoué")
            return False

    def save_report(self):
        """
        Sauvegarde le rapport des tests dans un fichier JSON
        """
        try:
            os.makedirs("logs", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"logs/jwt_test_report_{timestamp}.json"

            report = {
                "project": "XCSM",
                "date": time.strftime("%Y-%m-%d"),
                "base_url": BASE_URL,
                "results": self.results,
                "summary": {
                    "total": len(self.results),
                    "passed": sum(1 for r in self.results if r['success']),
                    "failed": sum(1 for r in self.results if not r['success'])
                }
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"Rapport sauvegardé: {filename}")
        except Exception as e:
            print(f"Note: Impossible de sauvegarder le rapport: {e}")

# -----------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# -----------------------------------------------------------------
if __name__ == "__main__":
    """
    Point d'entrée principal du script de test
    """
    print("Démarrage des tests d'authentification JWT...")

    test_suite = JWTTestSuite()
    success = test_suite.run_all_tests()

    # Nettoyage des fichiers temporaires
    test_file = Path("test_jwt_document.pdf")
    if test_file.exists():
        try:
            test_file.unlink()
            print(f"Fichier temporaire supprimé: {test_file}")
        except Exception as e:
            print(f"Note: Impossible de supprimer le fichier temporaire: {e}")

    if success:
        print("\nFin des tests - Code de sortie: 0 (SUCCÈS)")
        sys.exit(0)
    else:
        print("\nFin des tests - Code de sortie: 1 (ÉCHEC)")
        sys.exit(1)