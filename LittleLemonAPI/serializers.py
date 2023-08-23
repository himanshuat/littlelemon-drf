from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"
        depth = 1


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["title"]


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username']


class DeliveryCrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username']


class CartItemsSerializer(serializers.ModelSerializer):
    menuitem_id = serializers.PrimaryKeyRelatedField(
        queryset = MenuItem.objects.all(),
        source="menuitem",
        write_only=True
    )
    class Meta:
        model = Cart
        fields = ["menuitem", "menuitem_id", "quantity", "unit_price", "price"]
        read_only_fields = ["unit_price", "price"]
        depth = 1


class OrderSerializer(serializers.ModelSerializer):
    orderitems = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["user", "total", "date", "orderitems"]

    def get_orderitems(self, obj):
        orderitems = OrderItem.objects.filter(order=obj)
        serializer = OrderItemSerializer(orderitems, many=True, context={'request': self.context['request']})
        return serializer.data


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        depth = 1