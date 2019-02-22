# app/user/serializers.py
from django.contrib.auth import get_user_model, authenticate
# for outputting messages to screen. Supports multiple languages
from django.utils.translation import ugettext_lazy as _

# Import serializers from DRF so we can use ModelSerializer
from rest_framework import serializers


# Create a new serializer that inherits from ModelSerializer
class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    # Add class Meta
    class Meta:
        # Specify the model to base our ModelSerializer on first line
        model = get_user_model()
        # Specify the fields to include in the serializer. These are the
        # fields that will be converted to/from JSON when make our HTTP POST,
        # retrieve in our view, then save to our model
        fields = ('email', 'password', 'name')
        # Add extra_kwargs to config a few extra settings in ModelSerializer
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        # Call our custom create_user() function in order to create
        # encrypted password for the new user. Use **validated_data
        # to unwind validated_data into the params of create_user()
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, setting the password correctly and return it"""
        # Purpose of this is to ensure password is set using set_password()
        # Instance is the model instance linked to ModelSerializer (user)
        # Validated_data are the fields we defined in Meta
        # Let's first remove the password from validated_data
        password = validated_data.pop('password', None)
        # Call default update() w/ super() inside custom update()
        user = super().update(instance, validated_data)

        # Set password if user provides one
        if password:
            user.set_password(password)
            user.save()

        return user


# Create new serializer based on standard serializers module for auth requests
class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication object"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    # Check that inputs are correct by using standard validate()
    def validate(self, attrs):
        """Validate and authenticate the user"""
        # Retrieve email and password from attrs DICT
        email = attrs.get('email')
        password = attrs.get('password')
        # Validate whether to pass/fail by using authenticate. See notes.
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        # When authentication fails display message and error to user
        if not user:
            msg = _("Unable to authenticate with provided credentials")
            raise serializers.ValidationError(msg, code='authentication')
        # Authentication passes so set attrs['user'] to user object
        attrs['user'] = user
        # Must return alues at end when whenever overriding validate()
        return attrs
