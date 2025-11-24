from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Map "email" to the authentication username field
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(request=self.context['request'], username=email, password=password)
        if not user:
            self.error_messages['no_active_account'] = 'Invalid credentials'
            raise self.fail('no_active_account')
        data = super().validate({'username': email, 'password': password})
        return data

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer