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
    url(r'^renewals/$', views.view_renewals_report, name='consortial_renewals'),
    url(r'^renewals/start/(?P<start_date>\d{4}-\d{2}-\d{2})/end/(?P<end_date>\d{4}-\d{2}-\d{2})/$',
        views.view_renewals_report,
        name='consortial_renewals_with_date'),
    url(r'^renewals/(?P<billing_agent_id>\d+)/$', views.renewals_by_agent, name='consortial_renewals_agent'),

    url(r'^institution/new/$', views.institution_manager, name='consortial_institution'),
    url(r'^institution/(?P<institution_id>\d+)/$', views.institution_manager, name='consortial_institution_id'),

    url(r'^polling/new/$', views.polling_manager, name='consortial_polling'),
    url(r'^polling/(?P<poll_id>\d+)/$', views.polling_manager, name='consortial_polling_id'),
    url(r'^polling/(?P<poll_id>\d+)/option/(?P<option_id>\d+)/$', views.polling_manager,
        name='consortial_polling_option'),
    url(r'^polling/(?P<poll_id>\d+)/summary/$', views.poll_summary, name='consortial_polling_summary'),
    url(r'^polling/(?P<poll_id>\d+)/email/$', views.poll_email, name='consortial_polling_email'),

    url(r'^polls/$', views.polls, name='consortial_polls'),
    url(r'^polls/(?P<poll_id>\d+)/$', views.polls_vote, name='consortial_polls_vote'),
]
