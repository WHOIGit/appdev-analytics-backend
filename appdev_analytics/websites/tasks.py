from celery import shared_task

from .models import Website


@shared_task(time_limit=1800, soft_time_limit=1800, bind=True)
def download_data_update(self, site_id=None):
    print(site_id)
    if not site_id:
        return False

    try:
        site = Website.objects.get(id=site_id)
    except Website.DoesNotExist:
        return False

    site.update_download_data()
    print(f"{site} logs parsed")
    return True


@shared_task(time_limit=7200, soft_time_limit=7200)
def run_download_data_updates():
    sites = Website.objects.filter(is_active=True)
    for site in sites:
        print(f"{site} queued for processing - {site.id}")
        download_data_update.delay(site.id)
