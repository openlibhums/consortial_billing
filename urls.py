from django.conf.urls import url
from plugins.consortial_billing import views

urlpatterns = [
    url(r'^$', views.index, name='consortial_index'),
    url(r'^non_funding_author_insts/$', views.non_funding_author_insts, name='consortial_non_funding_author_insts'),
]
