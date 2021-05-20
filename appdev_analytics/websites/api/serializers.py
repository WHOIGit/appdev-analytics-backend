from django.db.models import Sum
from django.db.models.functions import TruncDay
from django.utils import timezone

from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer

from ..models import Website, DataPoint


class DataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPoint
        fields = ["date_logged", "url", "bytes_sent"]


class WebsiteSerializer(
    serializers.HyperlinkedModelSerializer, FlexFieldsModelSerializer
):
    ga_results = serializers.SerializerMethodField("get_ga_results")
    download_results = serializers.SerializerMethodField("get_download_data")
    total_daily_download_results = serializers.SerializerMethodField(
        "get_total_daily_download_data"
    )

    class Meta:
        model = Website
        fields = [
            "id",
            "url",
            "name",
            "domain",
            "download_results",
            "total_daily_download_results",
            "ga_results",
        ]
        extra_kwargs = {"url": {"view_name": "api:websites-detail"}}

    def get_ga_results(self, obj):
        query_params = self.context["query_params"]
        # setup GA API dimensions
        dimensions = query_params.get("dimensions", "country")
        dimensions = dimensions.split(",")
        # setup GA API metrics
        metrics = query_params.get("metrics", "activeUsers")
        metrics = metrics.split(",")
        # setup GA API start_date
        start_date = query_params.get("start_date", "90daysAgo")
        # setup GA API start_date
        end_date = query_params.get("end_date", "today")

        return obj.get_ga4_data(dimensions, metrics, start_date, end_date)

    def get_total_daily_download_data(self, obj):
        datapoints_qs = obj.datapoints.all()
        # group download date by Day, get sum of all downloads
        datapoints_qs = (
            datapoints_qs.annotate(date=TruncDay("date_logged"))
            .values("date")
            .annotate(bytes_sent_total=Sum("bytes_sent"))
            .order_by("date")
        )

        total_download_data = []
        for datapoint in datapoints_qs:
            date_str = datapoint["date"].isoformat()
            data_obj = {
                "date": date_str,
                "bytes_sent": datapoint["bytes_sent_total"],
            }
            total_download_data.append(data_obj)
        return total_download_data

    def get_download_data(self, obj):
        # Check if user wants to exclude datapoints
        exclude_dataseries = self.context.get("exclude_dataseries")
        if exclude_dataseries:
            return None

        # Otherwise create the datapoint series
        datapoints_qs = obj.datapoints.all()
        download_data = []

        for datapoint in datapoints_qs:
            date_str = datapoint.date_logged.isoformat()
            data_obj = {
                "date": date_str,
                "url": datapoint.url,
                "bytes_sent": datapoint.bytes_sent,
            }
            download_data.append(data_obj)

        return download_data
