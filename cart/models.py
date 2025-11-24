from django.conf import settings
from django.db import models
from product.models import Product

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='carts'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_cart', condition=models.Q(user__isnull=False)),
            models.UniqueConstraint(fields=['session_key'], name='unique_session_cart', condition=models.Q(session_key__isnull=False)),
        ]

    def __str__(self):
        return f"Cart({self.user or self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.product.price * item.quantity for item in self.items.select_related('product'))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"