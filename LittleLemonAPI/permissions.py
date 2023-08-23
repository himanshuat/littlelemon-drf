from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Manager").exists()
    

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Delivery crew").exists()
    

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name="Delivery crew").exists():
            return False
        elif request.user.groups.filter(name="Manager").exists():
            return False
        else:
            return True