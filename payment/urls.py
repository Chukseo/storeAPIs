from django.urls import path
from .views import CreatePaymentIntentView, PaymentWebhookView

urlpatterns = [
    path('create/<int:order_id>/', CreatePaymentIntentView.as_view(), name='payment-create'),
    path('webhook/<str:provider>/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
