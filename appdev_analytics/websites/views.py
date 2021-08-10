import boto3
import os
from pathlib import Path

# from django.shortcuts import render
from django.http import HttpResponse

# local app
from config.settings.base import env
from .models import Website

LOGS_DIR = "s3-logs"


def manual_download_data_updates(request):
    sites = Website.objects.all()
    for site in sites:
        if site.is_active:
            site.update_download_data()
    return HttpResponse("Log parsing complete")


def get_s3_files(request):
    file_dir = os.path.join(LOGS_DIR, "habhub.whoi.edu")
    # create site domain dir if not exists
    Path(file_dir).mkdir(parents=True, exist_ok=True)
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(env("AWS_STORAGE_BUCKET_NAME"))
    objects = bucket.objects.filter(Prefix="habhub.whoi.edu/")

    for obj in objects:
        print(obj)
        if obj.key.endswith((".log", ".gz")):
            path, filename = os.path.split(obj.key)
            bucket.download_file(obj.key, f"{file_dir}/{filename}")

    return HttpResponse("S3 connected")
