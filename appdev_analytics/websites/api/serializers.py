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
        dimensions = request_obj.query_params.get("dimensions", "country")
        dimensions = dimensions.split(",")
        print(dimensions)
        return obj.get_ga4_data(dimensions=dimensions)
