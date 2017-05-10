import re

from submission import models as submission_models
from core import models as core_models


def get_authors():
    authors = list()
    articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PUBLISHED)

    for article in articles:
        for author in article.authors.all():
            authors.append(author)

    return authors


def get_editors():
    editors = list()
    editorial_groups = core_models.EditorialGroup.objects.all()

    for group in editorial_groups:
        for member in group.members():
            editors.append(member.user)

    return editors


def users_not_supporting(institutions, authors, editors):
    authors_and_editors = list(set(authors + editors))
    institution_names = [inst.name for inst in institutions]

    for user in authors_and_editors:
        find = re.compile(".*?{0}.*".format(user.institution))
        print(filter(find.match, institution_names))
        if filter(find.match, institution_names):
            authors_and_editors.remove(user)
        else:
            print(user.full_name, user.institution, 'not matched')

    return authors_and_editors