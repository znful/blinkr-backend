from rest_framework.decorators import permission_classes
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.core.models import ShortURL
from apps.core.serializers import ShortURLSerializer


class ShortURLViewSet(viewsets.ModelViewSet):
    """
    ShortURL ViewSet for viewing, creating and editing ShortURLs.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ShortURLSerializer

    def get_queryset(self):
        return ShortURL.objects.filter(owner=self.request.user)
