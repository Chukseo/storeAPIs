from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CartItem
from .serializers import CartSerializer, CartItemSerializer
from .utils import get_or_create_session_cart, get_or_create_user_cart, merge_session_cart_into_user_cart
from product.models import Product
from django.db.models import Sum

from cart import models


class CartDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        items = cart.items.all()
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartAddItemView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # ✅ Fix: use models.Cart instead of cart.objects
        cart, created = models.Cart.objects.get_or_create(session_key=session_key)

        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        if quantity < 1:
            return Response({'detail': 'Quantity must be >= 1'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        item, created = cart.items.get_or_create(product=product, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartUpdateItemView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, item_id):
        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        try:
            item = cart.items.get(pk=item_id)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get('quantity', item.quantity))
        if quantity < 1:
            item.delete()
        else:
            item.quantity = quantity
            item.save()
        return Response(CartSerializer(cart).data)


class CartClearView(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request):
        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        cart.items.all().delete()
        return Response({'detail': 'Cart cleared'}, status=status.HTTP_204_NO_CONTENT)


class CartCheckoutPrepView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Merge session cart into user cart after login
        session_cart = get_or_create_session_cart(request)
        user_cart = get_or_create_user_cart(request.user)
        merge_session_cart_into_user_cart(session_cart, user_cart)
        return Response(CartSerializer(user_cart).data, status=status.HTTP_200_OK)


class CartCountView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        count = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        return Response({'count': count}, status=status.HTTP_200_OK)
