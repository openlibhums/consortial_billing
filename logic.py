import re

from plugins.consortial_billing import models
from submission import models as submission_models
from core import models as core_models


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