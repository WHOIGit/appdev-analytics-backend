import datetime
from rest_framework import viewsets
from django.utils import timezone
from django.db.models import Prefetch

from ..models import Website, DataPoint
from .serializers import WebsiteListSerializer, WebsiteDetailSerializer

default_start_date = timezone.now() - datetime.timedelta(days=90)
default_end_date = timezone.now()


class WebsiteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WebsiteListSerializer
    detail_serializer_class = WebsiteDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # context["django_url_arg"] = self.kwargs['django_url_arg']
        context["query_params"] = self.request.query_params
        return context

    # return different sets of fields if the request is list all or retrieve one,
    # so use two different serializers
    def get_serializer_class(self):
        if self.action == "retrieve":
            if hasattr(self, "detail_serializer_class"):
                return self.detail_serializer_class
        return super(WebsiteViewSet, self).get_serializer_class()

    def get_queryset(self):
        queryset = Website.objects.all()
        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)

        start_date_obj = default_start_date
        if start_date:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        end_date_obj = default_end_date
        if end_date:
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        queryset = queryset.prefetch_related(
            Prefetch(
                "datapoints",
                queryset=DataPoint.objects.filter(
                    date_logged__range=[start_date_obj, end_date_obj]
                ),
            )
        )
        return queryset
