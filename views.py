import csv
import io
import distutils.util
import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.utils import timezone
from django.core.cache import cache

from utils import setting_handler, function_cache
from plugins.consortial_billing import models, logic, plugin_settings, forms
from core import models as core_models

@staff_member_required
@function_cache.cache(900)
def index(request):
    if request.POST:
        # an action
        if 'csv_upload' in request.FILES:
            csv_import = request.FILES['csv_upload']
            csv_reader = csv.DictReader(io.StringIO(csv_import.read().decode('utf-8')))

            for row in csv_reader:
                # get the band
                band, created = models.Banding.objects.get_or_create(name=row["Banding"])

                if distutils.util.strtobool(row["Consortial Billing"]):
                    consortium, created = models.Institution.objects.get_or_create(name=row["Consortium"])
                else:
                    consortium = None

                if row["Billing Agent"] != '':
                    billing_agent, created = models.BillingAgent.objects.get_or_create(name=row["Billing Agent"])
                else:
                    billing_agent = None

                institution, created = models.Institution.objects.get_or_create(name=row["Institution Name"],
                                                                                country=row["Country"],
                                                                                active=row["Active"],
                                                                                consortial_billing=
                                                                                row["Consortial Billing"],
                                                                                consortium=consortium,
                                                                                banding=band,
                                                                                billing_agent=billing_agent)

                dict_renewal_amount = row.get("Renewal Amount")
                renewal_amount = dict_renewal_amount if dict_renewal_amount != '' else 0.00

                renewal = models.Renewal.objects.create(date=row["Renewal Date"],
                                                        amount=renewal_amount,
                                                        institution=institution,
                                                        currency=row["Currency"])

    near_renewals = models.Renewal.objects.filter(date__lte=timezone.now().date() + datetime.timedelta(days=31),
                                                  institution__active=True,
                                                  billing_complete=False).order_by('date')

    renewals_in_next_year = models.Renewal.objects.filter(date__lte=timezone.now().date() + datetime.timedelta(days=365),
                                                          institution__active=True,
                                                          billing_complete=False).values('currency').annotate(price=Sum('amount'))

    context = {'institutions': models.Institution.objects.all(),
               'renewals': near_renewals,
               'renewals_in_year': renewals_in_next_year,
               'plugin': plugin_settings.SHORT_NAME}

    return render(request, 'consortial_billing/admin.html', context)


def signup(request):
    signup_text = setting_handler.get_plugin_setting(plugin_settings.get_self(), 'preface_text', None)

    context = {'signup_text': signup_text}

    return render(request, 'consortial_billing/signup.html', context)


def signup_stage_two(request):
    bandings = models.Banding.objects.all().order_by('name', '-default_price')
    errors = list()

    if request.POST:
        banding_id = request.POST.get('banding')
        if banding_id:
            banding = get_object_or_404(models.Banding, pk=banding_id)
            return redirect(reverse('consortial_detail', kwargs={'banding_id': banding.pk}))
        else:
            banding = None
            errors.append('No banding has been selected')


    context = {
        'bandings': bandings,
        'errors': errors,
    }

    return render(request, 'consortial_billing/signup2.html', context)


def signup_complete(request):
    complete_text = setting_handler.get_plugin_setting(plugin_settings.get_self(), 'complete_text', None)

    context = {'complete_text': complete_text}

    return render(request, 'consortial_billing/complete.html', context)

def signup_stage_three(request, banding_id):
    banding = get_object_or_404(models.Banding, pk=banding_id)
    form = forms.Institution()

    if request.POST:
        form = forms.Institution(request.POST)
        if form.is_valid():
            institution = form.save(commit=False)
            institution.banding = banding
            institution.save()

            models.Renewal.objects.create(institution=institution,
                                          currency=banding.currency,
                                          amount=banding.default_price,
                                          date=timezone.now())

            logic.send_emails(institution, request)
            return redirect(reverse('consortial_complete'))


    context = {
        'banding': banding,
        'form': form,
    }

    return render(request, 'consortial_billing/signup3.html', context)


@staff_member_required
def non_funding_author_insts(request):
    if request.POST and 'user' in request.POST:
        user_id = request.POST.get('user')
        user = get_object_or_404(core_models.Account, pk=user_id)
        models.ExcludedUser.objects.get_or_create(user=user)
        messages.add_message(request, messages.INFO, "User has been excluded from this list.")
        return redirect(reverse('consortial_non_funding_author_insts'))

    institutions = models.Institution.objects.all()
    authors = logic.get_authors()
    editors = logic.get_editors()

    list_of_users_not_supporting = logic.users_not_supporting(institutions, authors, editors)

    template = 'consortial_billing/non_funding.html'
    context = {
        'authors_and_editors': list_of_users_not_supporting,
        'institutions': institutions,
    }

    return render(request, template, context)


def supporters(request):
    institutions = models.Institution.objects.filter(display=True)

    plugin = plugin_settings.get_self()
    pre_text = setting_handler.get_plugin_setting(plugin, 'pre_text', None)
    post_text = setting_handler.get_plugin_setting(plugin, 'post_text', None)

    template = 'consortial_billing/supporters.html'
    context = {
        'institutions': institutions,
        'pre_text': pre_text,
        'post_text': post_text
    }

    return render(request, template, context)


def process_renewal(request, renewal_id):
    renewal = get_object_or_404(models.Renewal, pk=renewal_id, billing_complete=False)
    renewal_form = forms.Renewal(institution=renewal.institution)

    if request.POST:
        renewal_form = forms.Renewal(request.POST)
        if renewal_form.is_valid():
            new_renewal = renewal_form.save(commit=False)
            new_renewal.institution = renewal.institution
            renewal.billing_complete = True
            renewal.date_renewed = timezone.now()

            new_renewal.save()
            renewal.save()
            cache.clear()

            messages.add_message(request, messages.SUCCESS, 'Renewal for {0} processed.'.format(renewal.institution))
            return redirect(reverse('consortial_index'))

    context = {
        'renewal': renewal,
        'renewal_form': renewal_form,
    }

    return render(request, 'consortial_billing/process_renewal.html', context)


def view_renewals_report(request, start_date=None, end_date=None):
    if request.POST:
        start = request.POST.get('start')
        end = request.POST.get('end')
        print(start)
        return redirect(reverse('consortial_renewals_with_date', kwargs={'start_date': start, 'end_date': end}))

    if not start_date:
        start_date = timezone.now() - datetime.timedelta(days=365)

    if not end_date:
        end_date = timezone.now()

    renewals = models.Renewal.objects.filter(billing_complete=True,
                                             date_renewed__gte=start_date,
                                             date_renewed__lte=end_date)

    template = 'consortial_billing/renewals_report.html'
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'renewals': renewals,
    }

    return render(request, template, context)
