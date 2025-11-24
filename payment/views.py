
from decimal import Decimal
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order
from .models import Payment
import requests
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        provider = request.data.get('provider')  # 'paystack' | 'stripe' | 'paypal'
        currency = request.data.get('currency', 'NGN')

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response({'detail': 'Order not pending'}, status=status.HTTP_400_BAD_REQUEST)

        amount = Decimal(order.total)

        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={'provider': provider, 'amount': amount, 'currency': currency, 'status': 'pending'}
        )
        payment.provider = provider
        payment.amount = amount
        payment.currency = currency
        payment.save()

        if provider == 'paystack':
            # Initialize transaction
            init_url = f"{settings.PAYSTACK_BASE_URL}/transaction/initialize"
            payload = {
                'email': request.user.email,
                'amount': int(amount * 100),  # kobo
                'currency': currency,
                'reference': f"ORDER_{order.id}"
            }
            headers = {'Authorization': f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            r = requests.post(init_url, json=payload, headers=headers, timeout=30)
            data = r.json()
            if r.status_code == 200 and data.get('status'):
                payment.provider_reference = data['data']['reference']
                payment.save()
                return Response({'authorization_url': data['data']['authorization_url']}, status=status.HTTP_200_OK)
            return Response({'detail': 'Paystack init failed', 'error': data}, status=status.HTTP_400_BAD_REQUEST)

        elif provider == 'stripe':
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                customer_email=request.user.email,
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {'name': f"Order #{order.id}"},
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                success_url=request.build_absolute_uri(f'/payments/stripe/success/{order.id}/'),
                cancel_url=request.build_absolute_uri(f'/payments/stripe/cancel/{order.id}/'),
            )
            payment.provider_reference = session.id
            payment.save()
            return Response({'checkout_session_id': session.id, 'url': session.url}, status=status.HTTP_200_OK)

        elif provider == 'paypal':
            # Create order via PayPal REST API
            access_token = self._paypal_access_token()
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
            payload = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': currency,
                        'value': str(amount)
                    },
                    'reference_id': f"ORDER_{order.id}"
                }],
                'application_context': {
                    'return_url': request.build_absolute_uri(f'/payments/paypal/success/{order.id}/'),
                    'cancel_url': request.build_absolute_uri(f'/payments/paypal/cancel/{order.id}/'),
                }
            }
            r = requests.post(f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders", json=payload, headers=headers, timeout=30)
            data = r.json()
            if r.status_code in (200, 201):
                payment.provider_reference = data['id']
                payment.save()
                approve_link = next((l['href'] for l in data['links'] if l['rel'] == 'approve'), None)
                return Response({'approve_url': approve_link, 'paypal_order_id': data['id']}, status=status.HTTP_200_OK)
            return Response({'detail': 'PayPal init failed', 'error': data}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'detail': 'Unsupported provider'}, status=status.HTTP_400_BAD_REQUEST)

    def _paypal_access_token(self):
        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials'}
        r = requests.post(f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token", headers=headers, data=data, auth=auth, timeout=30)
        r.raise_for_status()
        return r.json()['access_token']


class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]  # Webhooks come from providers, not user

    def post(self, request, provider):
        # Handle provider-specific webhook to mark order as paid/failed
        if provider == 'stripe':
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            sig = request.META.get('HTTP_STRIPE_SIGNATURE')
            payload = request.body
            try:
                event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                ref = session['id']
                payment = Payment.objects.filter(provider='stripe', provider_reference=ref).first()
                if payment:
                    payment.status = 'succeeded'
                    payment.save()
                    order = payment.order
                    order.status = 'paid'
                    order.save()
            return Response(status=status.HTTP_200_OK)

        elif provider == 'paystack':
            # Verify event and reference, then mark as succeeded
            data = request.data
            ref = data.get('data', {}).get('reference') or data.get('reference')
            payment = Payment.objects.filter(provider='paystack', provider_reference=ref).first()
            if payment and data.get('event') == 'charge.success':
                payment.status = 'succeeded'
                payment.save()
                order = payment.order
                order.status = 'paid'
                order.save()
            return Response(status=status.HTTP_200_OK)

        elif provider == 'paypal':
            # Capture completed signal via webhook (simulate basic)
            resource = request.data.get('resource', {})
            order_id = resource.get('id')
            payment = Payment.objects.filter(provider='paypal', provider_reference=order_id).first()
            if payment and request.data.get('event_type') == 'CHECKOUT.ORDER.APPROVED':
                # You should call capture API here to finalize payment
                payment.status = 'succeeded'
                payment.save()
                order = payment.order
                order.status = 'paid'
                order.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)