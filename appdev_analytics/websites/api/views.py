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
        start_date = self.request.query_params.get("startDate", None)
        end_date = self.request.query_params.get("endDate", None)

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

    def get_ga_results(self, obj):
        query_params = self.request.query_params
        # setup GA API dimensions
        dimensions = query_params.get("dimensions", "country")
        dimensions = dimensions.split(",")
        # setup GA API metrics
        metrics = query_params.get("metrics", "activeUsers,screenPageViews")
        metrics = metrics.split(",")
        # setup GA API start_date
        start_date = query_params.get("startDate", "90daysAgo")
        # setup GA API start_date
        end_date = query_params.get("endDate", "today")

        return obj.get_ga4_data(dimensions, metrics, start_date, end_date)
