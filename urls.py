from django.conf.urls import url
from plugins.consortial_billing import views

urlpatterns = [
    url(r'^$', views.index, name='consortial_index'),
]