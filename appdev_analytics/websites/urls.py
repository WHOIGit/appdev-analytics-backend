from django.urls import path

from appdev_analytics.websites.views import ParseNginxLogView, parse_nginx_to_pandas

app_name = "websites"
urlpatterns = [
    path("nginx/", view=ParseNginxLogView.as_view(), name="nginx"),
    path("nginx-pandas/", view=parse_nginx_to_pandas, name="nginx-pandas"),
]
