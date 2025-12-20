from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, health_check, login, dashboard

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check, name='health-check'),
    path('login/', login, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
]


