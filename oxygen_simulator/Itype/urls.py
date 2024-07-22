from django.urls import include, re_path
from . import views

urlpatterns = [
    re_path("editor",views.editor,name = 'editor'),
    # re_path("",views.data_path,name= 'datapath')
    re_path("datapath",views.datapath,name= 'datapath'),
    re_path("decoder",views.decoder,name='decoder'),
    re_path('request',views.request,name='request'),
    re_path('assemble-code/', views.assemble_code, name='assemble-code'),

]
