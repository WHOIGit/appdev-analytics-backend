import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import RunReportRequest

from django.db import models


class Website(models.Model):
    name = models.CharField(max_length=200, unique=False, db_index=True)
    url = models.URLField(max_length=200, unique=True)
    ga4_property_id = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_ga4_data(
        self,
        dimensions=["country"],
        metrics=["activeUsers"],
        start_date="2020-03-31",
        end_date="today",
    ):
        """Runs a report on a Google Analytics 4 property."""
        # Using a default constructor instructs the client to use the credentials
        # specified in GOOGLE_APPLICATION_CREDENTIALS environment variable.
        client = BetaAnalyticsDataClient()

        # ex. dimensions: date, city
        dimensions_formatted = []
        for dim in dimensions:
            new_dim = Dimension(name=dim)
            dimensions_formatted.append(new_dim)

        # ex. metrics: screenPageViews, activeUsers
        metrics_formatted = []
        for met in metrics:
            new_met = Metric(name=met)
            metrics_formatted.append(new_met)

        request = RunReportRequest(
            property=f"properties/{self.ga4_property_id}",
            dimensions=dimensions_formatted,
            metrics=metrics_formatted,
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        response = client.run_report(request)

        print("Report result:")
        for row in response.rows:
            for dimension_value in row.dimension_values:
                print(dimension_value.value)

            for metric_value in row.metric_values:
                print(metric_value.value)
            # print(row.dimension_values[0].value, row.metric_values[0].value)

        return response
