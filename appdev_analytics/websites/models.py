from datetime import datetime
import os
import gzip
import re
import pandas as pd

from django.db import models
from django.utils import timezone
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    MetricType,
    RunReportRequest,
)

INPUT_DIR = "logs"
lineformat_nginx = re.compile(
    r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""",
    re.IGNORECASE,
)


class Website(models.Model):
    name = models.CharField(max_length=200, unique=False, db_index=True)
    domain = models.CharField(max_length=200, unique=True)
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

        results = {
            "dimension_headers": [],
            "metric_headers": [],
            "rows": [],
        }

        for dimensionHeader in response.dimension_headers:
            results["dimension_headers"].append({"name": dimensionHeader.name})
            print(f"Dimension header name: {dimensionHeader.name}")

        for metricHeader in response.metric_headers:
            metric_type = MetricType(metricHeader.type_).name
            results["metric_headers"].append({"name": metricHeader.name})
            print(f"Metric header name: {metricHeader.name} ({metric_type})")

        for row in response.rows:
            dimension_values = []
            for dimension_value in row.dimension_values:
                dimension_values.append({"value": dimension_value.value})
                print(dimension_value.value)

            metric_values = []
            for metric_value in row.metric_values:
                metric_values.append({"value": metric_value.value})
                print(metric_value.value)
            # print(row.dimension_values[0].value, row.metric_values[0].value)
            results["rows"].append(
                {"dimension_values": dimension_values, "metric_values": metric_values}
            )
        return results

    def update_nginx_data(self):
        file_dir = os.path.join(INPUT_DIR, self.domain)
        logs_df = pd.DataFrame(
            {
                "dateandtime": [],
                "url": [],
                "bytessent": [],
            }
        )

        for f in os.listdir(file_dir):
            if f.endswith(".gz"):
                logfile = gzip.open(os.path.join(file_dir, f))
            else:
                logfile = open(os.path.join(file_dir, f))

            for line in logfile.readlines():
                data = re.search(lineformat_nginx, line)
                if data:
                    datadict = data.groupdict()
                    # ip = datadict["ipaddress"]
                    # referrer = datadict["refferer"]
                    # useragent = datadict["useragent"]
                    # status = datadict["statuscode"]
                    # method = data.group(6)
                    print(datadict["statuscode"])
                    if datadict["statuscode"] == "200":
                        # Converting string to datetime obj
                        datetimeobj = datetime.strptime(
                            datadict["dateandtime"], "%d/%b/%Y:%H:%M:%S %z"
                        )
                        # split url on query parameters, remove query
                        url = datadict["url"].split("?")[0].strip()
                        bytessent = datadict["bytessent"]
                        if not url.endswith((".css", ".js", ".ico")):
                            print(url)
                            logs_df = logs_df.append(
                                {
                                    "dateandtime": datetimeobj,
                                    "url": url,
                                    "bytessent": bytessent,
                                },
                                ignore_index=True,
                            )

            logfile.close

        logs_df["bytessent"] = logs_df["bytessent"].astype(int)
        new_df = logs_df.groupby(["url", pd.Grouper(key="dateandtime", freq="D")]).agg(
            {"bytessent": "sum"}
        )
        new_df.columns = ["bytessent"]
        new_df = new_df.reset_index()

        for index, row in new_df.iterrows():
            datapoint = DataPoint.objects.filter(
                date_logged=row["dateandtime"].date(), url=row["url"]
            ).last()

            if datapoint:
                # date/url combination already has a record, need to updated bytes_sent
                datapoint.bytes_sent = datapoint.bytes_sent + row["bytessent"]
                datapoint.save()
            else:
                # else create new Datapoint
                datapoint = DataPoint.objects.create(
                    website=self,
                    date_logged=row["dateandtime"].date(),
                    url=row["url"],
                    bytes_sent=row["bytessent"],
                )
        return "Data points updated"


class DataPoint(models.Model):
    website = models.ForeignKey(
        Website, on_delete=models.CASCADE, related_name="datapoints"
    )
    date_logged = models.DateField(default=timezone.now)
    url = models.CharField(max_length=1000)
    bytes_sent = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["date_logged"]
        get_latest_by = "date_logged"

    def __str__(self):
        return self.url
