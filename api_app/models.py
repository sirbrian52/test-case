# models.py

from django.db import models

class Customer(models.Model):
    customer_name = models.CharField(max_length=200)

    def __str__(self):
        return (f"{self.customer_name},{self.id}")

class Product(models.Model):
    product_code = models.CharField(max_length=15)
    product_name = models.CharField(max_length=250)
    product_price = models.FloatField()
    product_status = models.CharField(max_length=11, default='0')
    product_stock = models.IntegerField(default=0)

    def __str__(self):
        return self.product_name

class Sale(models.Model):
    sale_date = models.DateTimeField(null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    sale_items_total = models.IntegerField(default=0)
    transaction_code = models.CharField(max_length=50,default="N/A")

    def __str__(self):
        return self.transaction_code

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_price = models.FloatField()
    item_qty = models.IntegerField(default=0)
    is_verify = models.IntegerField(default=0)
