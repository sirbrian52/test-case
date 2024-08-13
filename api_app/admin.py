from django.contrib import admin
from api_app import models
# Register your models here.
admin.site.register(models.Customer)
admin.site.register(models.Sale)
admin.site.register(models.SaleItem)
admin.site.register(models.Product)
