from rest_framework.routers import DefaultRouter
from .views import ComplaintViewSet, EvidenceViewSet

router = DefaultRouter()
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'evidence',   EvidenceViewSet,  basename='evidence')

urlpatterns = router.urls
