from django.urls import include, path
from . import views

urlpatterns = [
    path('dump-code', views.assemble_code, name='assemble-code'),
    path('assemble-code', views.assemble_code, name='assemble-code'),
    path('step', views.step_code, name='step-code'),
    path('reset', views.reset, name='reset-code'),
]
