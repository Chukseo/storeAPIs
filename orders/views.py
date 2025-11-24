from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.utils import get_or_create_user_cart

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class CreateOrderFromCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = get_or_create_user_cart(request.user)
        if not cart.items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user)
        subtotal = 0

        for item in cart.items.select_related('product'):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                unit_price=item.product.price,
                quantity=item.quantity,
            )
            subtotal += item.product.price * item.quantity

        order.subtotal = subtotal
        order.total = subtotal  # adjust with shipping/tax if needed
        order.save()

        # Optionally clear cart
        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)