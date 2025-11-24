from .models import Cart

def get_or_create_session_cart(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart

def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user, session_key=None)
    return cart

def merge_session_cart_into_user_cart(session_cart, user_cart):
    for item in session_cart.items.all():
        target, created = user_cart.items.get_or_create(product=item.product, defaults={'quantity': item.quantity})
        if not created:
            target.quantity += item.quantity
            target.save()
    session_cart.delete()