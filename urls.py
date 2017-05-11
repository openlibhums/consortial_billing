from django.conf.urls import url
from plugins.consortial_billing import views

urlpatterns = [
    url(r'^$', views.supporters, name='consortial_supporters'),
    url(r'^admin/$', views.index, name='consortial_index'),

    url(r'^signup/$', views.signup, name='consortial_signup'),
    url(r'^signup/banding/$', views.signup_stage_two, name='consortial_banding'),
    url(r'^signup/banding/(?P<banding_id>\d+)/details/$', views.signup_stage_three, name='consortial_detail'),
    url(r'^signup/complete/$', views.signup_complete, name='consortial_complete'),

    url(r'^process_renewal/(?P<renewal_id>\d+)/$', views.process_renewal, name='consortial_process_renewal'),

    url(r'^non_funding_author_insts/$', views.non_funding_author_insts, name='consortial_non_funding_author_insts'),
]
