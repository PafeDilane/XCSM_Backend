# xcsm/permissions.py
"""
Permissions personnalisées pour XCSM avec support JWT
"""
from rest_framework import permissions


class IsAuthenticatedWithJWT(permissions.BasePermission):
    """
    Permission de base pour vérifier que l'utilisateur est authentifié via JWT
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsEnseignant(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les enseignants
    """
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type_compte == 'ENSEIGNANT'
        )


class IsEtudiant(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les étudiants
    """
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type_compte == 'ETUDIANT'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les administrateurs
    """
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type_compte == 'ADMIN'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission pour autoriser le propriétaire ou lecture seule
    """
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True

        # Vérifier si l'utilisateur est propriétaire
        if hasattr(obj, 'enseignant'):
            return obj.enseignant.utilisateur == request.user
        elif hasattr(obj, 'utilisateur'):
            return obj.utilisateur == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class CanAccessDocument(permissions.BasePermission):
    """
    Permission spécifique pour l'accès aux documents
    """
    def has_permission(self, request, view):
        # Les enseignants peuvent uploader
        if view.action == 'create':
            return (
                    request.user.is_authenticated and
                    request.user.type_compte == 'ENSEIGNANT'
            )
        # Tout utilisateur authentifié peut lire
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Le propriétaire ou un admin peut tout faire
        if obj.enseignant.utilisateur == request.user or request.user.type_compte == 'ADMIN':
            return True

        # Les autres utilisateurs ne peuvent que lire
        return request.method in permissions.SAFE_METHODS


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour autoriser le propriétaire ou un admin
    """
    def has_object_permission(self, request, view, obj):
        if request.user.type_compte == 'ADMIN':
            return True

        if hasattr(obj, 'enseignant'):
            return obj.enseignant.utilisateur == request.user
        elif hasattr(obj, 'utilisateur'):
            return obj.utilisateur == request.user

        return False