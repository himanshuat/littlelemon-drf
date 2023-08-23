from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework import status

from .models import *
from .serializers import *
from .permissions import *

import datetime


class CategoryView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [IsAdminUser]


class ListMenuItems(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    search_fields = ["title", "category__title"]
    ordering_fields = ["price", "category"]

    def get_permissions(self):
        permission_classes = []
        if self.request.method != "GET":
            permission_classes = [IsAdminUser, IsManager]
        return [permission() for permission in permission_classes]


class SingleMenuItem(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        permission_classes = []
        if self.request.method != "GET":
            permission_classes = [IsAdminUser, IsManager]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ListManagers(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name="Manager")
    serializer_class = ManagerSerializer
    permission_classes = [IsAdminUser, IsManager]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name="Manager")
            managers.user_set.add(user)
            return Response(
                status=status.HTTP_201_CREATED,
                data={"message": "User added to Managers"},
            )
        return Response(
            status=status.HTTP_404_NOT_FOUND, data={"message": "User not found"}
        )


class SingleManager(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name="Manager")
    serializer_class = ManagerSerializer
    permission_classes = [IsAdminUser, IsManager]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def delete(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return Response(
            status=status.HTTP_200_OK, data={"message": "User removed from Managers"}
        )


class ListDeliveryCrew(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name="Delivery crew")
    serializer_class = DeliveryCrewSerializer
    permission_classes = [IsAdminUser, IsManager]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name="Delivery crew")
            managers.user_set.add(user)
            return Response(
                status=status.HTTP_201_CREATED,
                data={"message": "User added to Delivery crew"},
            )
        return Response(
            status=status.HTTP_404_NOT_FOUND, data={"message": "User not found"}
        )


class SingleDeliveryCrew(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name="Delivery crew")
    serializer_class = DeliveryCrewSerializer
    permission_classes = [IsAdminUser, IsManager]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def delete(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name="Delivery crew")
        managers.user_set.remove(user)
        return Response(
            status=status.HTTP_200_OK,
            data={"message": "User removed from Delivery crew"},
        )


class CartItems(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartItemsSerializer
    permission_classes = [IsAdminUser, IsCustomer]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(MenuItem, pk=request.data["menuitem_id"])
        try:
            newitem = Cart(
                user=request.user,
                menuitem=item,
                quantity=request.data["quantity"],
                unit_price=item.price,
                price=int(request.data["quantity"]) * item.price,
            )
            newitem.save()
        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Item already exists in cart"},
            )
        return Response(
            status=status.HTTP_201_CREATED, data={"message": "Item added to cart"}
        )

    def delete(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        cart.delete()
        return Response(status=status.HTTP_200_OK, data={"message: Cart items cleared"})


class ListOrders(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        if self.request.user.groups.filter(name="Delivery crew").exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        elif self.request.user.groups.filter(name="Manager").exists():
            return Order.objects.all()
        else:
            return Order.objects.filter(user=self.request.user)

    def get_permissions(self):
        permission_classes = []
        if self.request.method == "POST":
            permission_classes = [IsAdminUser, IsAuthenticated & IsCustomer]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        if len(cart) == 0:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Empty cart! Add items to cart to place order"},
            )

        total = sum([float(item.price) for item in cart])
        order = Order(user=request.user, status=False, total=total)
        order.save()

        for item in cart:
            orderitem = OrderItem(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price,
            )
            orderitem.save()

        cart.delete()

        return Response(
            status=status.HTTP_201_CREATED,
            data={"message": f"Your order has been placed. ID: {order.pk}"},
        )


class SingleOrder(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        order = Order.objects.get(pk=self.kwargs["pk"])
        permission_classes = []

        if self.request.method == "PATCH":
            permission_classes += [
                IsAuthenticated & IsDeliveryCrew,
                IsAuthenticated & IsManager,
            ]
        elif self.request.method == "PUT":
            permission_classes += [IsAuthenticated & IsManager]
        elif self.request.method == "DELETE":
            permission_classes += [IsAuthenticated & IsManager]
        elif self.request.method == "GET" and self.request.user == order.user:
            permission_classes += [IsCustomer | IsDeliveryCrew | IsManager]
        else:
            permission_classes += []

        return [permission() for permission in permission_classes]

    def get_queryset(self, *args, **kwargs):
        return Order.objects.filter(pk=self.kwargs["pk"])

    def put(self, request, *args, **kwargs):
        order_pk = self.kwargs["pk"]
        crew_pk = request.data["delivery_crew"]
        order = get_object_or_404(Order, pk=order_pk)
        crew = get_object_or_404(User, pk=crew_pk)
        order.delivery_crew = crew
        order.save()
        return Response(
            status=status.HTTP_200_OK,
            data={"message": f"Order (ID: {order.pk}) has been updated"},
        )

    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs["pk"])
        order.status = not order.status
        order.save()
        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": f"Status of order (ID: {order.id}) has changed to {order.status}"
            },
        )

    def delete(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs["pk"])
        order.delete()
        return Response(
            status=status.HTTP_200_OK,
            data={"message": f"Order with ID: {self.kwargs['pk']} has been deleted"},
        )
