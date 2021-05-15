# from django.shortcuts import render
from django.http import HttpResponse

# local app
from .models import Website


def parse_nginx_to_pandas(request):
    site = Website.objects.get(id=2)
    site.update_nginx_data()
    return HttpResponse("Cool stuff")
