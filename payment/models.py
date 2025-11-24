from django.conf import settings
from django.db import models
from orders.models import Order

class Payment(models.Model):
    PROVIDER_CHOICES = (
        ('paystack', 'Paystack'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    )

    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')  # Stripe/PayPal may use 'USD', etc.
    status = models.CharField(max_length=20, default='pending')  # pending, succeeded, failed
    provider_reference = models.CharField(max_length=255, blank=True)  # transaction id/session id
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider} payment for Order #{self.order_id}"