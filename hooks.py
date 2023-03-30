from django.urls import reverse
from django.template.loader import render_to_string

from utils import setting_handler
from utils.function_cache import cache


@cache(300)
def nav_hook(context):
    supporters_url = reverse('consortial_supporters')
    signup_url = reverse('consortial_signup')
    leader_url = reverse('referral_leadership_board')
    referral_url = reverse('referral_codes')
    request = context['request']

    short_org_name = setting_handler.get_setting(
        'plugin:consortial_billing',
        'organisation_short_name',
        None,
    )

    display_nav = setting_handler.get_setting(
        'plugin:consortial_billing',
        'display_nav',
        None,
    ).processed_value

    display_leader = setting_handler.get_setting(
        'plugin:consortial_billing',
        'leader_board',
        None,
    ).processed_value

    display_referral = setting_handler.get_setting(
        'plugin:consortial_billing',
        'display_referral',
        None,
    ).processed_value

    journals_setting = setting_handler.get_setting(
        'plugin:consortial_billing',
        'journal_display',
        None,
    ).value

    if not display_nav:
        return ''

    journal_pks = []
    if journals_setting and journals_setting != ' ':
        journal_pks = [int(pk) for pk in journals_setting.split(',')]
    if (
        request.journal and request.journal.id in journal_pks
    ) or (
        not request.journal and request.press
    ):
        item = {
            'link_name': 'Support {0}'.format(short_org_name.value),
            'link': '',
            'has_sub_nav': True,
            'sub_nav_items': [
                {'link_name': 'Library Sign Up',
                 'link': signup_url},
                {'link_name': 'Supporting Institutions',
                 'link': supporters_url}
            ]
        }
        if display_referral:
            item['sub_nav_items'].append(
                {'link_name': 'Referrals', 'link': referral_url}
            )
        if display_referral and display_leader:
            item['sub_nav_items'].append(
                {'link_name': 'Referral Leader Board', 'link': leader_url}
            )

        nav = render_to_string('elements/nav_element.html', {'item': item})

        return nav
    return ''


def admin_hook(context):
    return '''
           <li>
             <a href="{url}">
               <i class="fa fa-money"></i>
               Consortial Billing
             </a>
           </li>
           '''.format(url=reverse('consortial_index'))
