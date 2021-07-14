from celery import shared_task

from .models import Website


@shared_task(time_limit=7200, soft_time_limit=7200)
def run_download_data_updates():
    sites = Website.objects.filter(is_active=True)
    for site in sites:
        site.update_download_data()
        print(f"{site} logs parsed")
