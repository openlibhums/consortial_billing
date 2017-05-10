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
                print(row["Institution Name"])
                print(row["Renewal Amount"])
                print(row["Currency"])
                print(row["Renewal Date"])
                print(row["Country"])
                print(row["Banding"])
                print(row["Active"])
                print(row["Consortium"])
                print(row["Consortial Billing"])
                print(row["Billing Agent"])

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