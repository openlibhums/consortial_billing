from utils import notify_helpers


def email_agent_about_signup(**kwargs):
    request = kwargs['request']
    supporter = kwargs['supporter']

    supporter_url = request.build_absolute_uri(supporter.url)
    description = f'New signup: {supporter.name} ({supporter_url})'

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Supporter Signup',
        'target': supporter,
    }

    to = [user.email for user in supporter.band.billing_agent.users.all()]
    context = {
        'supporter': supporter,
        'supporter_url': supporter_url,
    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'new_signup_email',
        'subject_new_signup_email',
        to,
        context,
        log_dict=log_dict,
    )


def email_supporter_to_confirm(**kwargs):
    request = kwargs['request']
    supporter = kwargs['supporter']

    supporter_url = request.build_absolute_uri(supporter.url)
    description = f'''
        Confirmation email to supporter:
        {supporter.name} ({supporter_url})
    '''

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Supporter Confirmation',
        'target': supporter,
    }

    to = [user.email for user in supporter.contacts.all()]
    context = {
        'supporter': supporter,
    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'signup_confirmation_email',
        'subject_signup_confirmation_email',
        to,
        context,
        log_dict=log_dict,
    )
