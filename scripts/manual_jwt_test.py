"""
Tests automatisés et manuels JWT - XCSM Project

Ce script teste les fonctionnalités principales du module d'authentification XCSM :
1. Inscription utilisateur
2. Connexion et génération de tokens JWT
3. Rafraîchissement des tokens
4. Accès au profil utilisateur
5. Upload de documents protégés
6. Déconnexion
7. Désactivation de compte
8. Suppression définitive de compte
9. Vérification de l'archivage et de la suppression des données

Usage :
    python test_xcsm_auth.py

Auteur : Team XCSM 4GI ENSPY
"""

import requests
import json
import sys
import re
from pathlib import Path
from datetime import datetime

# -----------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------

BASE_URL = "http://localhost:8000/api/v1"
tokens = {}

USERNAME_REGEX = r'^[\w.@+-]+$'
EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'

# -----------------------------------------------------------------
# OUTILS UTILITAIRES
# -----------------------------------------------------------------

def print_title(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def pause():
    input("\nAppuyez sur Entrée pour continuer...")

def ask_input(label, validator=None, error_msg="", optional=False):
    """
    Saisie sécurisée avec validation immédiate
    """
    while True:
        value = input(f"{label} : ").strip()
        if value == "0":
            return None
        if not value and not optional:
            print("Champ obligatoire.")
            continue
        if validator and value and not validator(value):
            print(error_msg)
            continue
        return value

def print_response(response):
    print(f"\nCode HTTP : {response.status_code}")
    try:
        print("Réponse :", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print("Réponse brute :", response.text)

def save_tokens(data):
    """
    Sauvegarde localement les tokens JWT
    """
    tokens["access"] = data.get("access")
    tokens["refresh"] = data.get("refresh")
    print("\nTokens enregistrés localement.")
    print("Access :", tokens["access"][:40], "...")
    print("Refresh:", tokens["refresh"][:40], "...")


# -----------------------------------------------------------------
# ACTIONS AUTHENTIFICATION
# -----------------------------------------------------------------

def register(username=None, email=None, password=None, type_compte="ETUDIANT"):
    """
    Inscription utilisateur
    """
    print_title("INSCRIPTION UTILISATEUR (0 pour annuler)")

    if username is None:
        username = ask_input(
            "Username",
            lambda v: re.match(USERNAME_REGEX, v),
            "Format invalide. Utilisez lettres, chiffres et @ . + - _ uniquement."
        )
        if username is None: return

    if email is None:
        email = ask_input(
            "Email",
            lambda v: re.match(EMAIL_REGEX, v),
            "Email invalide."
        )
        if email is None: return

    if password is None:
        password = ask_input("Mot de passe")
        if password is None: return

    confirm = ask_input("Confirmer mot de passe")
    if confirm is None: return
    if password != confirm:
        print("Les mots de passe ne correspondent pas.")
        return

    first_name = ask_input("Prénom")
    last_name = ask_input("Nom")

    data = {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": confirm,
        "type_compte": type_compte,
        "first_name": first_name,
        "last_name": last_name
    }

    response = requests.post(f"{BASE_URL}/auth/register/", json=data)
    print_response(response)

    if response.status_code == 201:
        save_tokens(response.json())


def login(username=None, password=None):
    """
    Connexion utilisateur
    """
    print_title("CONNEXION (0 pour annuler)")

    if username is None:
        username = ask_input("Username")
        if username is None: return
    if password is None:
        password = ask_input("Mot de passe")
        if password is None: return

    response = requests.post(f"{BASE_URL}/auth/login/", json={"username": username, "password": password})
    print_response(response)

    if response.status_code == 200:
        save_tokens(response.json())


def refresh_token():
    """
    Rafraîchissement token
    """
    print_title("RAFRAÎCHISSEMENT TOKEN")
    if "refresh" not in tokens:
        print("Aucun refresh token disponible.")
        return
    response = requests.post(f"{BASE_URL}/auth/refresh/", json={"refresh": tokens["refresh"]})
    print_response(response)
    if response.status_code == 200:
        tokens["access"] = response.json()["access"]
        print("Access token mis à jour.")


def profile():
    """
    Accès au profil protégé
    """
    print_title("ACCÈS PROFIL UTILISATEUR")
    if "access" not in tokens:
        print("Vous devez être connecté.")
        return
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    response = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
    print_response(response)


def upload_document():
    """
    Upload de document pédagogique
    """
    print_title("UPLOAD DOCUMENT")
    if "access" not in tokens:
        print("Vous devez être connecté.")
        return
    file_path = Path("manual_test_doc.txt")
    file_path.write_text("Document de test JWT manuel", encoding="utf-8")

    with open(file_path, "rb") as f:
        headers = {"Authorization": f"Bearer {tokens['access']}"}
        response = requests.post(
            f"{BASE_URL}/documents/upload/",
            headers=headers,
            files={"fichier_original": f},
            data={"titre": "Document manuel", "description": "Upload CLI"}
        )
    print_response(response)
    file_path.unlink()


def logout():
    """
    Déconnexion
    """
    print_title("DÉCONNEXION")
    if "refresh" not in tokens:
        print("Aucun utilisateur connecté.")
        return
    headers = {"Authorization": f"Bearer {tokens.get('access','')}"}
    response = requests.post(f"{BASE_URL}/auth/logout/", json={"refresh": tokens["refresh"]}, headers=headers)
    print_response(response)
    tokens.clear()
    print("Déconnexion effectuée.")


# -----------------------------------------------------------------
# SUPPRESSION ET DÉSACTIVATION DE COMPTE
# -----------------------------------------------------------------

def deactivate_account():
    """
    Désactive le compte de l'utilisateur actuel
    """
    print_title("DÉSACTIVATION DE COMPTE")
    if "access" not in tokens:
        print("Vous devez être connecté.")
        return
    password = ask_input("Mot de passe actuel")
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    response = requests.put(
        f"{BASE_URL}/auth/deactivate-account/",
        headers=headers,
        json={"password": password, "reason": "Test automatique"}
    )
    print_response(response)
    logout()


def delete_account():
    """
    Supprime définitivement le compte de l'utilisateur actuel
    """
    print_title("SUPPRESSION DÉFINITIVE DE COMPTE")
    if "access" not in tokens:
        print("Vous devez être connecté.")
        return
    password = ask_input("Mot de passe actuel")
    confirmation = ask_input("Tapez 'JE_SUPPRIME_MON_COMPTE' pour confirmer")
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    response = requests.delete(
        f"{BASE_URL}/auth/delete-account/",
        headers=headers,
        json={"password": password, "confirmation": confirmation}
    )
    print_response(response)
    logout()


# -----------------------------------------------------------------
# MENU PRINCIPAL
# -----------------------------------------------------------------

def menu():
    while True:
        print_title("MENU TEST JWT - XCSM")
        print("1 - Inscription")
        print("2 - Connexion")
        print("3 - Rafraîchir token")
        print("4 - Accès profil protégé")
        print("5 - Upload document")
        print("6 - Déconnexion")
        print("7 - Désactiver compte")
        print("8 - Supprimer compte définitivement")
        print("0 - Quitter")

        choice = input("\nChoix : ").strip()
        actions = {
            "1": register,
            "2": login,
            "3": refresh_token,
            "4": profile,
            "5": upload_document,
            "6": logout,
            "7": deactivate_account,
            "8": delete_account
        }
        if choice == "0":
            print("\nFin des tests JWT.")
            sys.exit(0)
        action = actions.get(choice)
        if action:
            action()
            pause()
        else:
            print("Choix invalide.")
            pause()


# -----------------------------------------------------------------
# POINT D’ENTRÉE
# -----------------------------------------------------------------

if __name__ == "__main__":
    menu()
