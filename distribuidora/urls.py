from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, VendedorViewSet


router = DefaultRouter()

router.register(
    r'clientes',
    ClienteViewSet,
    basename='cliente'
)

router.register(
    r'vendedores',
    VendedorViewSet,
    basename='vendedor'
)

urlpatterns = router.urls