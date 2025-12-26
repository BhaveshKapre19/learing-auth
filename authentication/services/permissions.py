#authentication/permission.py


from rest_framework.permissions import BasePermission , SAFE_METHODS


class HasTemporaryPassword(BasePermission):
    """if the user is loged in and has temp password enable they need to change the password"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return not request.user.has_temp_password
            

class IsActiveUser(BasePermission):
    """checks if the user is active or not"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active
    

class IsEmailVerified(BasePermission):
    """checks the user for the verified emails"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_email_verified


class RequiresTempPassword(BasePermission):
    """checks if the user has a temporary password"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.has_temp_password
        )

    
