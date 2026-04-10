"""
URL configuration for simulaciones_pequiven project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from .views import *

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Bienvenida.as_view(), name='bienvenida'),
    path('logout/', CerrarSesion.as_view(), name='cerrar_sesion'),
    path('login/', Login.as_view(), name='iniciar_sesion'),
    path('plantas/', PlantasPorComplejo.as_view(), name="plantas_por_complejo"),

    path('intercambiadores/', include('intercambiadores.urls')),
    path('auxiliares/', include('auxiliares.urls')),
    path('turbinas/', include('turbinas.urls')),
    path('calderas/', include('calderas.urls')),
    path('compresores/', include('compresores.urls')),

    path('usuarios/', include('usuarios.urls')),
    path('', include('pwa.urls')),
    path('manual/', ManualDeUsuario.as_view(), name="manual"),
    # path("__debug__/", include("debug_toolbar.urls")),

    path('plantas/consulta/', ConsultaPlantas.as_view(), name="consulta_plantas"),
    path('plantas/creacion/', CreacionPlanta.as_view(), name="creacion_planta"),
    path('plantas/edicion/<int:pk>', EdicionPlanta.as_view(), name="edicion_planta"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)