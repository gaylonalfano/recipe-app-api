# app/recipe/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views


# Create a new router object
router = DefaultRouter()
# Register our TagViewSet with our router
router.register('tags', views.TagViewSet)
# Register our IngredientViewSet with our router
router.register('ingredients', views.IngredientViewSet)
# Register our RecipeViewSet with our router
router.register('recipes', views.RecipeViewSet)


# Define app_name so reverse() can look up correct urls
app_name = 'recipe'

# Define our urlpatterns
urlpatterns = [
    # Pass our router-generated URLs to be included in urlpatterns
    path('', include(router.urls))
]
