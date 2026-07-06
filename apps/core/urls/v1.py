from rest_framework import routers
from apps.core.views.v1 import ShortURLViewSet

router = routers.SimpleRouter()
router.register(r"", ShortURLViewSet, basename="shorturl")
urlpatterns = router.urls
