from rest_framework import viewsets
from ..models import Website
from .serializers import WebsiteSerializer


class WebsiteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset that provides Read Only actions
    """

    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
