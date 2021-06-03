# from django.shortcuts import render
from django.http import HttpResponse

# local app
from .models import Website


def parse_nginx_to_pandas(request):
    sites = Website.objects.all()
    for site in sites:
        if site.is_active:
            site.update_download_data()
    return HttpResponse("Log parsing complete")
