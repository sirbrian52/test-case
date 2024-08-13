import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project.settings')
django.setup()

from api_app.models import Customer, Product, Sale, SaleItem
from django.utils import timezone

# Data untuk dimasukkan
customers = [
    {'customer_name': 'CUSTOMER A'},
    {'customer_name': 'CUSTOMER B'},
    {'customer_name': 'CUSTOMER C'},
    {'customer_name': 'CUSTOMER D'},
    {'customer_name': 'CUSTOMER E'},
    {'customer_name': 'CUSTOMER F'},
]

products = [
    {'product_code': 'PRD0000000001', 'product_name': 'NASI GORENG', 'product_price': 13000, 'product_status': 'Active', 'product_stock': 50},
    {'product_code': 'PRD0000000002', 'product_name': 'BAKMI AYAM', 'product_price': 12000, 'product_status': 'Active', 'product_stock': 200},
    {'product_code': 'PRD0000000003', 'product_name': 'NASI PADANG', 'product_price': 17000, 'product_status': 'Active', 'product_stock': 300},
    {'product_code': 'PRD0000000004', 'product_name': 'AYAM PENYET', 'product_price': 18000, 'product_status': 'Active', 'product_stock': 400},
    {'product_code': 'PRD0000000005', 'product_name': 'PECEL AYAM', 'product_price': 22000, 'product_status': 'Active', 'product_stock': 120},
    {'product_code': 'PRD0000000006', 'product_name': 'PECEL BEBEK', 'product_price': 30000, 'product_status': 'Active', 'product_stock': 130},
    {'product_code': 'PRD0000000007', 'product_name': 'PECEL LELE', 'product_price': 18000, 'product_status': 'Active', 'product_stock': 140},
    {'product_code': 'PRD0000000008', 'product_name': 'JAGUNG BAKAR', 'product_price': 7000, 'product_status': 'Active', 'product_stock': 150},
    {'product_code': 'PRD0000000009', 'product_name': 'TEH HANGAT', 'product_price': 5000, 'product_status': 'Active', 'product_stock': 160},
    {'product_code': 'PRD0000000010', 'product_name': 'JAHE HANGAT', 'product_price': 8000, 'product_status': 'Active', 'product_stock': 170},
    {'product_code': 'PRD0000000011', 'product_name': 'AIR MINERAL MERK A', 'product_price': 4000, 'product_status': 'Active', 'product_stock': 180},
    {'product_code': 'PRD0000000012', 'product_name': 'KOPI HITAM', 'product_price': 3000, 'product_status': 'Active', 'product_stock': 190},
    {'product_code': 'PRD0000000013', 'product_name': 'TEH HUJAU', 'product_price': 9000, 'product_status': 'hold', 'product_stock': 220},
    {'product_code': 'PRD0000000014', 'product_name': 'TELUR REBUS', 'product_price': 4000, 'product_status': 'hold', 'product_stock': 0},
    {'product_code': 'PRD0000000015', 'product_name': 'KAMBING GULING', 'product_price': 120000, 'product_status': 'hold', 'product_stock': 3},
]


# Menambahkan data
for cust in customers:
    Customer.objects.create(**cust)

for prod in products:
    Product.objects.create(**prod)

"""for sale in sales:
    Sale.objects.create(**sale)

for item in sale_items:
    SaleItem.objects.create(**item)"""
