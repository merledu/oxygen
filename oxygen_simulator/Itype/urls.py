from django.urls import include, path
from . import views

urlpatterns = [
    path("",views.editor,name = 'editor'),
    # re_path("",views.data_path,name= 'datapath')
    path('assemble-code', views.assemble_code, name='assemble-code'),
    path('get-memory-values', views.get_memory_values, name='get_memory_values'),

]
