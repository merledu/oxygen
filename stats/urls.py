from django.urls import include, path
from . import views

urlpatterns = [
    path('assemble-code', views.gen_stats, name='assemble-code'),
]
