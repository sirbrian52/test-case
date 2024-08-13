from rest_framework import serializers
from .models import Customer, Sale, SaleItem, Product

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'customer_name']
        read_only_fields = ['id']

class SaleItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='product.id')
    price = serializers.FloatField(source='product_price')
    qty = serializers.IntegerField(source='item_qty')

    class Meta:
        model = SaleItem
        fields = ['id', 'price', 'qty']

class SaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.customer_name', read_only=True)
    items = SaleItemSerializer(source='saleitem_set', many=True)

    class Meta:
        model = Sale
        fields = ['customer','customer_name', 'transaction_code', 'sale_date', 'items']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
    