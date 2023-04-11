from django.conf.urls import re_path

from plugins.consortial_billing import views

urlpatterns = [
    re_path(
        r'^$',
        views.supporters,
        name='consortial_supporters',
    ),
    re_path(
        r'^support-bands/$',
        views.view_support_bands,
        name='view_support_bands',
    ),
    re_path(
        r'^site/(?P<page_name>.*)/$',
        views.view_custom_page,
        name='supporters_custom_page',
    ),
    re_path(
        r'^signup/$',
        views.signup,
        name='consortial_signup',
    ),
]
