from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet

router = DefaultRouter()

router.register(r'^tags', TagViewSet, basename='tags')
router.register(r'^ingredients', IngredientViewSet,
                basename='ingredients')
router.register(r'^recipes', RecipeViewSet, basename='recipes')

urlpatterns = router.urls
