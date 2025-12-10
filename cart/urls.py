from django.urls import path
from .views import CartDetailView, CartAddItemView, CartUpdateItemView, CartClearView, CartCheckoutPrepView, CartCountView

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart-detail'),
    path('add/', CartAddItemView.as_view(), name='cart-add'),
    path('item/<int:item_id>/', CartUpdateItemView.as_view(), name='cart-item-update'),
    path('clear/', CartClearView.as_view(), name='cart-clear'),
    path('checkout/prep/', CartCheckoutPrepView.as_view(), name='cart-checkout-prep'),
    path('cart/count/', CartCountView.as_view(), name='cart-count'),
]