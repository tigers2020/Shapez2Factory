from django.urls import path

from django_apps.game_data.browse import views

app_name = "game_data_browse"

urlpatterns = [
    path("browse/", views.game_data_browse, name="index"),
]
