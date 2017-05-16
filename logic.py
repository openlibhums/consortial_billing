import re
import datetime

from django.conf import settings
from django.utils import timezone
from django.db.models import Sum

from plugins.consortial_billing import models
from submission import models as submission_models
from core import models as core_models
from utils import notify_helpers, function_cache


def get_authors():
    authors = list()
    excluded_users = [user.user for user in models.ExcludedUser.objects.all()]
    articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PUBLISHED)

    for article in articles:
        for author in article.authors.all():
            if author not in excluded_users:
                authors.append(author)

    return authors


def get_editors():
    editors = list()
    excluded_users = [user.user for user in models.ExcludedUser.objects.all()]
    editorial_groups = core_models.EditorialGroup.objects.all()

    for group in editorial_groups:
        for member in group.members():
            if member.user not in excluded_users:
                editors.append(member.user)

    return editors


def users_not_supporting(institutions, authors, editors):

    authors_and_editors = list(set(authors + editors))
    institution_names = [inst.name for inst in institutions]

    authors_and_editors_output = list(set(authors + editors))

    print(institution_names)

    for user in authors_and_editors:
        find = re.compile(".*?{0}.*".format(user.institution.split(',')[0]))
        if len(list(filter(find.match, institution_names))) > 0:
            authors_and_editors_output.remove(user)

    return authors_and_editors_output


def send_emails(institution, request):
    message = 'A new supporting institution has registered. <a href=\"{0}{1}\">View information</a>'.format(
        settings.DEFAULT_HOST,
        '/plugins/supporters/admin/'
    )

    if institution.banding.billing_agent:
        emails = [user.email for user in institution.banding.billing_agent.users.all()]
        notify_helpers.send_email_with_body_from_user(request, 'New Supporting Institution', emails, message)


def get_users_agencies(request):
    if request.user.is_staff:
        return models.BillingAgent.objects.all()
    else:
        return models.BillingAgent.objects.filter(users__id__exact=request.user.pk)


@function_cache.cache(120)
def get_institutions_and_renewals(agent_for):
    near_renewals = models.Renewal.objects.filter(date__lte=timezone.now().date() + datetime.timedelta(days=31),
                                                  institution__active=True,
                                                  institution__billing_agent__in=agent_for,
                                                  billing_complete=False).order_by('date')

    renewals_in_next_year = models.Renewal.objects.filter(
        date__lte=timezone.now().date() + datetime.timedelta(days=365),
        institution__active=True,
        institution__billing_agent__in=agent_for,
        billing_complete=False).values('currency').annotate(price=Sum('amount'))
    institutions = models.Institution.objects.filter(billing_agent__in=agent_for)

    return near_renewals, renewals_in_next_year, institutions


def complete_all_renewals(renewals):
    renewal_date = timezone.now() + datetime.timedelta(days=334)

    for renewal in renewals:
        new_renewal = models.Renewal(date=renewal_date,
                                     amount=renewal.institution.banding.default_price,
                                     currency=renewal.institution.banding.currency,
                                     institution=renewal.institution)
        renewal.billing_complete = True
        renewal.date_renewed = timezone.now()

        new_renewal.save()
        renewal.save()