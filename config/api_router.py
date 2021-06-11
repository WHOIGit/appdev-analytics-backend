from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from appdev_analytics.websites.api.views import WebsiteViewSet
from appdev_analytics.users.api.views import UserViewSet

"""
if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()
"""
router = DefaultRouter()
router.register(r"websites", WebsiteViewSet, "websites")
router.register("users", UserViewSet)


app_name = "api"
urlpatterns = router.urls
