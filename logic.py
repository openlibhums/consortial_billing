from django.urls import reverse

from utils import models as utils_models


def get_signup_email_content(request, institution, currency, amount, host, url, display, user):
    plugin = utils_models.Plugin.objects.filter(
        name=plugin_settings.SHORT_NAME
    )
    context = {'institution': institution, 'currency': currency, 'amount': amount, 'host': host, 'url': url,
               'display': display, 'user': user}

    return render_template.get_message_content(request, context, 'new_signup_email', plugin=plugin)


def send_emails(institution, currency, amount, display, request):

    if institution.banding.billing_agent:
        users = [user for user in institution.banding.billing_agent.users.all()]
        users = users + [user for user in core_models.Account.objects.filter(is_superuser=True)]

        if request.journal:
            host = request.journal_base_url
        else:
            host = request.press_base_url

        url = reverse('consortial_institution_id', kwargs={'institution_id': institution.pk})

        for user in users:
            message = get_signup_email_content(request, institution, currency, amount, host, url, display, user)
            notify_helpers.send_email_with_body_from_user(request,
                                                          'New Supporting Institution for {0}'.format(request.press.name),
                                                          user.email, message)
