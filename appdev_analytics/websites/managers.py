from django.db import models
from django.db.models import Subquery, OuterRef, Sum
from django.db.models.functions import TruncDay
from django.apps import apps


class WebsiteQuerySet(models.QuerySet):
    def add_bytes_sum(self, date_q_filters=None):
        DataPoint = apps.get_model(app_label="websites", model_name="DataPoint")
        # set up the Subquery query with conditional date filter
        datapoint_query = DataPoint.objects.filter(website=OuterRef("id"))

        if date_q_filters:
            datapoint_query = datapoint_query.filter(date_q_filters)

        # now get the Sume
        datapoint_query = (
            datapoint_query.annotate(date=TruncDay("date_logged"))
            .values("date")
            .annotate(total_bytes_sent=Sum("bytes_sent"))
        )

        return self.annotate(bytes_total=Subquery(datapoint_query))
