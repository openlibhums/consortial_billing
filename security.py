from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from security.decorators import base_check
from plugins.consortial_billing import models


def billing_agent_required(func):
    """
    Checks if the current user is a billing agent.
    :return: the called function
    """

    def wrapper(request, *args, **kwargs):
        base_check(request)

        test = models.BillingAgent.objects.filter(users__id__exact=request.user.pk)

        if not test:
            raise PermissionDenied

        return func(request, *args, **kwargs)

    return wrapper


def billing_agent_for_institution_required(func):
    """
    Checks that a user is a billing agent for an institution
    :param func: called function
    :return: called function
    """

    def wrapper(request, *args, **kwargs):
        base_check(request)

        agent_for = models.BillingAgent.objects.filter(users__id__exact=request.user.pk)

        institution_id = kwargs.get('institution_id', None)
        renewal_id = kwargs.get('renewal_id')

        if request.user.is_staff:
            return func(request, *args, **kwargs)

        if institution_id:
            institution = get_object_or_404(models.Institution, pk=institution_id)

            if institution.billing_agent in agent_for:
                return func(request, *args, **kwargs)

        if renewal_id:
            renewal = get_object_or_404(models.Renewal, pk=renewal_id)

            if renewal.institution.billing_agent in agent_for:
                return func(request, *args, **kwargs)

        raise PermissionDenied

    return wrapper