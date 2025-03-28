from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("process/", views.process_text, name="process"),
    path("history/", views.history, name="history"),
    path("detail/<int:pk>/", views.detail, name="detail"),
    path("delete/<int:pk>/", views.delete, name="delete"),
    path("play/<int:pk>/", views.play_audio, name="play_audio"),
]
