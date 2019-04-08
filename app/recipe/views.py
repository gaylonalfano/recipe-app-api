# app/recipe/views.py
# Add custom action to ViewSet with action
from rest_framework.decorators import action
# Use Response to return custom responses
from rest_framework.response import Response
# See notes Section 12
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient, Recipe

from recipe import serializers


class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin):
    """Base viewset (common Tags/Ingr) for user owned recipe attributes"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    # We ignore queryset and serializer since they are unique

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        # Adding assigned_only for filtering functionality. Add 0 for default
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset

        # Add condition if assigned_only is True then apply filter
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        # Modify to return our filtered queryset (remove self, add distinct())
        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()

    def perform_create(self, serializer):
        """Create a new object"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""
    # add queryset we want to return
    queryset = Tag.objects.all()
    # add serializer class
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database"""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database. ModelViewSet allows users full func"""
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, querystring):
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in querystring.split(',')]

    # Override (I think) get_queryset to limit objects to auth user
    def get_queryset(self):
        """Retrieve the recipes for the authenticated user"""
        # Retrieve GET params provided in request (if any)
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        # Assign queryset instead of self.queryset. Read notes!
        queryset = self.queryset
        # Convert string IDs to list of integers (if any)
        if tags:
            # Convert string to int values
            tag_ids = self._params_to_ints(tags)
            # Filter queryset by using FK id on remote tags table. Read notes!
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            # Convert string to int values
            ingredient_ids = self._params_to_ints(ingredients)
            # Filter queryset by using FK id on remote ingredients table
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        # Reference self.queryset, apply filters, return new queryset
        return queryset.filter(user=self.request.user)

    # Override the serializer that is called when making a particular request
    # Check self.action class var.retrieve' = Detail, 'list' = default
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        # Check if action is upload image and use RecipeImageSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        # Retrieve the recipe object based on the id in url. Read NOTES!
        recipe = self.get_object()
        # Use the get_serializer() to retrieve and pass in our recipe data
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        # Check if serializer is valid. save() Recipe model with updated data
        if serializer.is_valid():
            serializer.save()
            # Return serializer object that was uploaded (recipe id image url)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        # Return default error messages if invalid
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
