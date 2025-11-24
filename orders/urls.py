# orders/urls.py
from django.urls import path
from .views import OrderListView, CreateOrderFromCartView, OrderDetailView

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderFromCartView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
]