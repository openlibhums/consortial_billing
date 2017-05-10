from django.http import HttpResponse
from django.shortcuts import render

import csv


def index(request):
    if request.POST:
        # an action
        if 'import_csv' in request.POST and len(request.FILES) > 0:
            csv_import = request.FILES[0]
            csv_reader = csv.DictReader(csv_import.chunks, delimeter=',')

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
