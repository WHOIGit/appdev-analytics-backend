from django.urls import path

from appdev_analytics.websites.views import manual_download_data_updates, get_s3_files

app_name = "websites"
urlpatterns = [
    path(
        "manual-data-update/",
        view=manual_download_data_updates,
        name="manual-data-update",
    ),
    path("get-s3/", view=get_s3_files, name="get-s3"),
]
