import re
import datetime

from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import get_object_or_404

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


def handle_polls_post(request, polls):

    poll_id = request.POST.get('poll')
    email = request.POST.get('email')

    poll = get_object_or_404(models.Poll, pk=poll_id,
                             date_open__lte=timezone.now(),
                             date_close__gte=timezone.now()
                             )

    try:
        institution = models.Institution.objects.get(email_address__iexact=email)
    except (models.Institution.DoesNotExist, models.Institution.MultipleObjectsReturned):
        institution = None

    try:
        vote = models.Vote.objects.filter(institution=institution)
    except models.Vote.DoesNotExist:
        vote = False

    return institution, poll, vote


def assign_cookie_for_vote(request, poll_id, institution_id):
    request.session['consortial_voting'] = {'poll': poll_id, 'institution': institution_id}
    request.session.modified = True


def get_inst_and_poll_from_session(request):
    if request.session.get('consortial_voting', None):
        poll_id = request.session['consortial_voting'].get('poll')
        institution_id = request.session['consortial_voting'].get('institution')

        poll = models.Poll.objects.get(pk=poll_id)
        inst = models.Institution.objects.get(pk=institution_id)

        try:
            vote = models.Vote.objects.filter(institution=inst)
        except models.Vote.DoesNotExist:
            vote = False

        return poll, inst, vote

    else:
        return None, None, False


@function_cache.cache(60)
def vote_count(poll):
    votes = models.Vote.objects.filter(poll=poll)
    vote_list = list()
    all_count = 0

    for option in poll.options.all():
        count = 0
        for vote in votes:
            count = count + vote.aye.filter(text=option.text).count()

        _dict = {
            'text': option.text,
            'count': count,
            'option': option,
        }

        vote_list.append(_dict)

        if option.all:
            all_count = all_count + count

    for _dict in vote_list:
        if _dict['count'] + all_count > votes.count() / 2:
            _dict['carried'] = True
        else:
            _dict['carried'] = False

    return vote_list, all_count


def process_poll_increases(options):
    renewals = models.Renewal.objects.filter(billing_complete=False)
    bandings = models.Banding.objects.all()

    for option in options:
        for renewal in renewals:
            increase = models.IncreaseOptionBand.objects.get(option=option, banding=renewal.institution.banding)
            print("Increasing renewal for {0} [Band {1}] by {2} {3} for option {4}".format(renewal.institution,
                                                                                    renewal.institution.banding.name,
                                                                                    increase.price_increase,
                                                                                    renewal.institution.banding.currency,
                                                                                    option.text))
            renewal.amount = float(renewal.amount) + float(increase.price_increase)
            renewal.save()

        for banding in bandings:
            increase = models.IncreaseOptionBand.objects.get(option=option, banding=banding)
            print("Increasing banding {0} by {1} {2} for option {3}".format(banding.name,
                                                                            banding.currency,
                                                                            increase.price_increase,
                                                                            option.text))
            banding.default_price = float(banding.default_price) + float(increase.price_increase)
            banding.save()
