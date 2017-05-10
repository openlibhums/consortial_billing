import csv
import io

import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.urlresolvers import reverse
import distutils.util

from django.utils import timezone

from plugins.consortial_billing import models, logic
from core import models as core_models


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

    near_renewals = models.Renewal.objects.filter(date__lte=timezone.now().date() + datetime.timedelta(1*365/12),
                                                  institution__active=True).order_by('date')
    context = {'institutions': models.Institution.objects.all(),
               'renewals': near_renewals}

    return render(request, 'consortial_billing/admin.html', context)


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