from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from security.decorators import base_check
from plugins.consortial_billing import models


def billing_agent_required(func):
    """
    Checks if the current user is a billing agent.
    :return: the called function
    """

    def wrapper(request, *args, **kwargs):

        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        agent_for = models.BillingAgent.objects.filter(users__id__exact=request.user.pk)

        if not agent_for and not request.user.is_staff:
            raise PermissionDenied

        return func(request, *args, **kwargs)

    return wrapper
