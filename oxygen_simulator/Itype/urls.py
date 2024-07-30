from django.urls import include, re_path
from . import views

urlpatterns = [
    re_path("editor",views.editor,name = 'editor'),
    # re_path("",views.data_path,name= 'datapath')
    re_path('assemble-code', views.assemble_code, name='assemble-code'),
    re_path('get-memory-values', views.get_memory_values, name='get_memory_values'),

]
