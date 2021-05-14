import os
import re
import pandas as pd
from datetime import datetime

# from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View

INPUT_DIR = "logs"

lineformat = re.compile(
    r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""",
    re.IGNORECASE,
)


def parse_nginx_to_pandas(request):
    # logs_df = pd.DataFrame(columns=["datetime", "url", "bytessent"])
    logs_df = pd.DataFrame(
        {
            "dateandtime": [],
            "url": [],
            "bytessent": [],
        }
    )
    for f in os.listdir(INPUT_DIR):
        logfile = open(os.path.join(INPUT_DIR, f))

        for line in logfile.readlines():
            data = re.search(lineformat, line)
            if data:
                datadict = data.groupdict()
                ip = datadict["ipaddress"]
                # Converting string to datetime obj
                datetimeobj = datetime.strptime(
                    datadict["dateandtime"], "%d/%b/%Y:%H:%M:%S %z"
                )
                url = datadict["url"]
                bytessent = datadict["bytessent"]
                referrer = datadict["refferer"]
                useragent = datadict["useragent"]
                status = datadict["statuscode"]
                method = data.group(6)
                logs_df = logs_df.append(
                    {"dateandtime": datetimeobj, "url": url, "bytessent": bytessent},
                    ignore_index=True,
                )
                # logs_df.append([dateandtime, url, bytessent])
        logfile.close

    logs_df["bytessent"] = logs_df["bytessent"].astype(float)
    logs_df = logs_df.groupby(pd.Grouper(key="dateandtime", freq="D")).sum()
    for index, row in logs_df.iterrows():
        print(index, row["bytessent"])
    return HttpResponse("Cool stuff")


# Parse nginx logs
class ParseNginxLogView(View):
    def get(self, request):
        # f = open("/logs/access.log")
        for f in os.listdir(INPUT_DIR):
            logfile = open(os.path.join(INPUT_DIR, f))

            for line in logfile.readlines():
                data = re.search(lineformat, line)
                if data:
                    datadict = data.groupdict()
                    ip = datadict["ipaddress"]
                    # Converting string to datetime obj
                    datetimeobj = datetime.strptime(
                        datadict["dateandtime"], "%d/%b/%Y:%H:%M:%S %z"
                    )
                    url = datadict["url"]
                    bytessent = datadict["bytessent"]
                    referrer = datadict["refferer"]
                    useragent = datadict["useragent"]
                    status = datadict["statuscode"]
                    method = data.group(6)

                    print(
                        ip,
                        datetimeobj,
                        url,
                        bytessent,
                        referrer,
                        useragent,
                        status,
                        method,
                    )
            logfile.close

        return HttpResponse("Cool stuff")
