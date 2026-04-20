from rest_framework.routers import DefaultRouter
from .views import ComplaintViewSet, EvidenceViewSet, SLAAlertViewSet, CommuneMetricViewSet

router = DefaultRouter()
router.register(r'complaints', ComplaintViewSet,    basename='complaint')
router.register(r'evidence',   EvidenceViewSet,     basename='evidence')
router.register(r'alerts',     SLAAlertViewSet,     basename='alert')
router.register(r'metrics',    CommuneMetricViewSet, basename='metric')

urlpatterns = router.urls
