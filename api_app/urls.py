from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (CustomerViewSet,
                    ProductViewSet,
                    SaleViewSet,
                    PagingViewSet,
                    CartCompareViewSet,
                    ProductPopulerViewSet,)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'sales', SaleViewSet, basename='sales')
router.register(r'paging', PagingViewSet, basename='paging')
router.register(r'cart_compare', CartCompareViewSet, basename='cart compare')
router.register(r'top_5_popular', ProductPopulerViewSet, basename='top 5 popular')

urlpatterns = [
    path('', include(router.urls)),
]