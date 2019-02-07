# app/user/views.py
# Import CreateAPIView
from rest_framework import generics
# Import ObtainAuthToken view since we need to customize it since no username
from rest_framework.authtoken.views import ObtainAuthToken
# Import our API settings
from rest_framework.settings import api_settings

# Import our serializers we created
from user.serializers import UserSerializer, AuthTokenSerializer


# Create our view using pre-made CreateAPIView
# This view allows us to easily make API that creates an object
# in a database using the serializer we provide
class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    # Only need to create a class variable that points to the
    # serializer we want to use to create the object. That's it!
    serializer_class = UserSerializer

class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""
    serializer_class = AuthTokenSerializer
    # Use default renderer classes so we have a browsable API
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
