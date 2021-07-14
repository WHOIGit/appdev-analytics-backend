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

HOST = r"^(?P<host>.*?)"
SPACE = r"\s"
IDENTITY = r"\S+"
USER = r"\S+"
TIME = r"(?P<dateandtime>\[.*?\])"
REQUEST = r"\"(?P<url>.*?)\""
STATUS = r"(?P<statuscode>\d{3})"
SIZE = r"(?P<bytessent>\S+)"

REGEX = (
    HOST
    + SPACE
    + IDENTITY
    + SPACE
    + USER
    + SPACE
    + TIME
    + SPACE
    + REQUEST
    + SPACE
    + STATUS
    + SPACE
    + SIZE
    + SPACE
)

lineformat_apache = re.compile(REGEX)
lineformat_nginx = re.compile(
    r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\S+")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""",
    re.IGNORECASE,
)


class Website(models.Model):
    class LogType(models.TextChoices):
        APACHE = "1", "Apache"
        NGINX = "2", "NGINX"

    name = models.CharField(max_length=200, unique=False, db_index=True)
    domain = models.CharField(max_length=200, unique=True)
    ga4_property_id = models.CharField(max_length=200, blank=True)
    log_type = models.CharField(
        max_length=32, choices=LogType.choices, default=LogType.APACHE
    )
    is_active = models.BooleanField(default=True)

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

        results = {
            "dimension_headers": [],
            "metric_headers": [],
            "rows": [],
        }

        try:
            response = client.run_report(request)
        except Exception as e:
            print(e)
            return results

        for dimensionHeader in response.dimension_headers:
            results["dimension_headers"].append({"name": dimensionHeader.name})

        for metricHeader in response.metric_headers:
            metric_type = MetricType(metricHeader.type_).name
            results["metric_headers"].append({"name": metricHeader.name})

        for row in response.rows:
            dimension_values = []
            for dimension_value in row.dimension_values:
                dimension_values.append({"value": dimension_value.value})

            metric_values = []
            for metric_value in row.metric_values:
                metric_values.append({"value": metric_value.value})

            # print(row.dimension_values[0].value, row.metric_values[0].value)
            results["rows"].append(
                {"dimension_values": dimension_values, "metric_values": metric_values}
            )
        return results

    def update_download_data(self):
        file_dir = os.path.join(INPUT_DIR, self.domain)

        if self.log_type == self.LogType.APACHE:
            lineformat = lineformat_apache
        elif self.log_type == self.LogType.NGINX:
            lineformat = lineformat_nginx

        logs_df = pd.DataFrame(
            {
                "dateandtime": [],
                "url": [],
                "bytessent": [],
            }
        )

        for f in os.listdir(file_dir):
            print("LOG FILE ", os.path.join(file_dir, f))
            try:
                logfile = None
                if f.endswith(".gz"):
                    logfile = gzip.open(os.path.join(file_dir, f), "rt")
                else:
                    logfile = open(os.path.join(file_dir, f))

                for line in logfile.readlines():
                    data = re.search(lineformat, line)
                    print(data)
                    if data:
                        datadict = data.groupdict()
                        print(datadict)
                        # ip = datadict["ipaddress"]
                        # referrer = datadict["refferer"]
                        # useragent = datadict["useragent"]
                        # status = datadict["statuscode"]
                        # method = data.group(6)
                        if datadict["statuscode"] == "200":
                            # check that bytes is an integer
                            try:
                                bytessent = int(datadict["bytessent"])
                            except Exception as e:
                                continue
                            # Converting string to datetime obj
                            datetimeobj = (
                                datadict["dateandtime"]
                                .replace("[", "")
                                .replace("]", "")
                            )
                            datetimeobj = datetime.strptime(
                                datetimeobj, "%d/%b/%Y:%H:%M:%S %z"
                            )

                            url = datadict["url"].strip()

                            if self.log_type == self.LogType.APACHE:
                                url = datadict["url"].split(" ")[1]
                            # split url on query parameters, remove query
                            url = url.split("?")[0]

                            if not url.endswith(
                                (".css", ".js", ".ico", ".map", ".php")
                            ):
                                logs_df = logs_df.append(
                                    {
                                        "dateandtime": datetimeobj,
                                        "url": url,
                                        "bytessent": bytessent,
                                    },
                                    ignore_index=True,
                                )

                logfile.close
            except Exception as e:
                print("ERROR ", e)
                continue

        if not logs_df.empty:
            logs_df["bytessent"] = logs_df["bytessent"].astype(int)
            new_df = logs_df.groupby(
                ["url", pd.Grouper(key="dateandtime", freq="D")]
            ).agg(
                {
                    "bytessent": "sum",
                    "dateandtime": "count",
                }
            )
            new_df.columns = ["bytessent", "hits"]
            new_df = new_df.reset_index()

            for index, row in new_df.iterrows():
                datapoint = self.datapoints.filter(
                    date_logged=row["dateandtime"].date(), url=row["url"]
                ).last()

                if datapoint:
                    # date/url combination already has a record, need to update bytes_sent/hits
                    datapoint.bytes_sent = datapoint.bytes_sent + row["bytessent"]
                    datapoint.hits = datapoint.hits + row["hits"]
                    datapoint.save()
                else:
                    # else create new Datapoint
                    datapoint = DataPoint.objects.create(
                        website=self,
                        date_logged=row["dateandtime"].date(),
                        url=row["url"],
                        bytes_sent=row["bytessent"],
                        hits=row["hits"],
                    )
        return "Data points updated"


class DataPoint(models.Model):
    website = models.ForeignKey(
        Website, on_delete=models.CASCADE, related_name="datapoints"
    )
    date_logged = models.DateTimeField(default=timezone.now)
    url = models.CharField(max_length=1000)
    bytes_sent = models.PositiveBigIntegerField()
    hits = models.PositiveIntegerField()

    class Meta:
        ordering = ["date_logged"]
        get_latest_by = "date_logged"

    def __str__(self):
        return self.url
