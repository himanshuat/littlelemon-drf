from django.urls import path
from .views import *

urlpatterns = [
    path("menu-items", ListMenuItems.as_view()),
    path("menu-items/<str:pk>", SingleMenuItem.as_view()),
    path("categories", CategoryView.as_view()),
    path("groups/manager/users", ListManagers.as_view()),
    path("groups/manager/users/<str:pk>", SingleManager.as_view()),
    path("groups/delivery-crew/users", ListDeliveryCrew.as_view()),
    path("groups/delivery-crew/users/<str:pk>", SingleDeliveryCrew.as_view()),
    path("cart/menu-items", CartItems.as_view()),
    path("orders", ListOrders.as_view()),
    path("orders/<str:pk>", SingleOrder.as_view()),
]
