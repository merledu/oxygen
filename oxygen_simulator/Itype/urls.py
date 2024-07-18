from django import path
from . import views

urlpatterns = [
    path("",views.home,name = 'home')
]
