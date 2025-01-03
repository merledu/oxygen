"""
URL configuration for oxygen_simulator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from Itype.views import *

urlpatterns = [
    path('oxygen/admin/', admin.site.urls),
    path('oxygen/' , include('Itype.urls')),
    path('oxygen/gen-hex/' , include(('hex_dump.urls','hex_dump'),namespace = 'hex_dump')),
    path('oxygen/gen-stats/' , include(('stats.urls','stats'),namespace = 'stats')),
    
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
