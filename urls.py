from django.conf.urls import url

from plugins.generic_plugin import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]