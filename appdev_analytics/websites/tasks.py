from celery import shared_task

from .models import Website


@shared_task(time_limit=300, soft_time_limit=300)
def run_download_data_updates():
    sites = Website.objects.all()
    for site in sites:
        if site.is_active:
            site.update_download_data()
            print(f"{site} logs parsed")
