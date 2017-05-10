import csv
from django.shortcuts import render

from plugins.consortial_billing import models, logic
import io

def index(request):
    if request.POST:
        # an action
        if 'csv_upload' in request.FILES:
            csv_import = request.FILES['csv_upload']
            csv_reader = csv.DictReader(io.StringIO(csv_import.read().decode('utf-8')))

            for row in csv_reader:
                # get the band
                band = models.Banding.objects.get_or_create(name=row["Banding"])

                if bool(row["Consortial Billing"]):
                    consortium, created = models.Institution.objects.get_or_create(name=row["Consortium"])
                else:
                    consortium, created = None

                if row["Billing Agent"] != '':
                    billing_agent, created = models.BillingAgent.objects.get_or_create(name=row["Billing Agent"])
                else:
                    billing_agent, created = None

                institution, created = models.Institution.objects.get_or_create(name=row["Institution Name"],
                                                                                country=row["Country"],
                                                                                active=row["Active"],
                                                                                consortial_billing=
                                                                                row["Consortial Billing"],
                                                                                consortium=consortium,
                                                                                banding=band,
                                                                                billing_agent=billing_agent)

                renewal = models.Institution.objects.create(date=row["Renewal Date"],
                                                            amount=row["Renewal Amount"],
                                                            institution=institution,
                                                            currency=row["Currency"])

    return render(request, 'consortial_billing/admin.html', {})


def non_funding_author_insts(request):
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