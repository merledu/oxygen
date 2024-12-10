from django.urls import include, path
from . import views

urlpatterns = [
    path("test",views.editor,name = 'editor'),
    path('',views.testpage,name='test_frontend'),
    # re_path("",views.data_path,name= 'datapath')
    path('run-code', views.run_code, name='assemble-code'),
    path('dump-code', views.assemble_code, name='assemble-code'),
    path('assemble-code', views.assemble_code, name='assemble-code'),
    path('step', views.step_code, name='step-code'),
    path('reset', views.reset, name='reset-code'),
]
