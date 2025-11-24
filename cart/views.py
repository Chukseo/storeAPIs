from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CartItem
from .serializers import CartSerializer, CartItemSerializer
from .utils import get_or_create_session_cart, get_or_create_user_cart, merge_session_cart_into_user_cart
from product.models import Product

class CartDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_session_cart(request) if not request.user.is_authenticated else get_or_create_user_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartAddItemView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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