from rest_framework import serializers
from ..models import Website


class WebsiteSerializer(serializers.ModelSerializer):
    ga_results = serializers.SerializerMethodField("get_ga_results")

    class Meta:
        model = Website
        fields = ["id", "name", "url", "ga_results"]

    def get_ga_results(self, obj):
        # get the request object to access query params
        request_obj = self.context["request"]
        # setup GA API dimensions
        dimensions = request_obj.query_params.get("dimensions", "country")
        dimensions = dimensions.split(",")
        # setup GA API metrics
        metrics = request_obj.query_params.get("metrics", "activeUsers")
        metrics = metrics.split(",")
        # setup GA API start_date
        start_date = request_obj.query_params.get("start_date", "90daysAgo")
        # setup GA API start_date
        end_date = request_obj.query_params.get("start_date", "today")

        return obj.get_ga4_data(dimensions, metrics, start_date, end_date)
