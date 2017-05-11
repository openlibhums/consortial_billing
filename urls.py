from django.conf.urls import url
from plugins.consortial_billing import views

urlpatterns = [
    url(r'^admin/$', views.index, name='consortial_index'),
    url(r'^signup/$', views.configure_signup, name='consortial_configure_signup'),
    url(r'^non_funding_author_insts/$', views.non_funding_author_insts, name='consortial_non_funding_author_insts'),
    url(r'^$', views.supporters, name='consortial_supporters'),
]
