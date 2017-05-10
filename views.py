from django.shortcuts import render

from plugins.consortial_billing import models, logic


def index(request):
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

