from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'provider', 'amount', 'currency', 'status', 'provider_reference', 'created_at')
    list_filter = ('provider', 'status')
    search_fields = ('provider_reference',)