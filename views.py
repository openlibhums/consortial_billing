from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.management import call_command

from plugins.consortial_billing import utils, \
     models, plugin_settings, forms, security
from plugins.consortial_billing.notifications import notify

from cms import models as cms_models
from utils.logger import get_logger
from security.decorators import base_check_required

logger = get_logger(__name__)


@security.billing_agent_required
def manager(request):

    if request.POST:
        if 'fetch_data' in request.POST:
            indicator = request.POST.get('fetch_data', None)
            call_command('fetch_world_bank_data', indicator)

        if 'recalculate_bands' in request.POST:
            call_command('calculate_all_fees', '--save')

    base_band = utils.get_base_band()
    latest_gni_data = utils.get_latest_gni_data()
    latest_exchange_rate_data = utils.get_latest_exchange_rate_data()
    exchange_rates = utils.get_exchange_rates_for_display()
    settings = utils.get_settings_for_display()

    context = {
        'plugin': plugin_settings.SHORT_NAME,
        'supporters': models.Supporter.objects.all(),
        'agents': models.BillingAgent.objects.all(),
        'sizes': models.Supporter.objects.all(),
        'levels': models.SupportLevel.objects.all(),
        'currencies': models.Currency.objects.all(),
        'base_band': base_band,
        'complete_text': utils.setting('complete_text'),
        'latest_gni_data': latest_gni_data,
        'latest_exchange_rate_data': latest_exchange_rate_data,
        'exchange_rates': exchange_rates,
        'settings': settings,
    }

    template = 'consortial_billing/manager.html'

    return render(request, template, context)


@base_check_required
def signup(request):

    band_form = forms.BandForm()
    band = None
    supporter_form = forms.SupporterForm()
    supporter = None
    signup_agreement = utils.setting('signup_agreement')
    complete_text = ''

    # This handles the redirect from custom CMS pages with a GET
    # calculation form
    if request.GET:
        band_form = forms.BandForm(request.GET)
        if band_form.is_valid():
            band = band_form.save(commit=False)
            band_form = forms.BandForm(
                instance=band,
            )
            supporter_form = forms.SupporterForm(
                {'band': band}
            )

    if request.POST:
        if 'calculate' in request.POST:
            band_form = forms.BandForm(request.POST)
            if band_form.is_valid():
                band = band_form.save(commit=False)
                band_form = forms.BandForm(
                    instance=band,
                )

                supporter_form = forms.SupporterForm(request.POST)

        if 'sign_up' in request.POST:
            band_form = forms.BandForm(request.POST)
            if band_form.is_valid():
                band = band_form.save(commit=True)
                band_form = forms.BandForm(
                    instance=band,
                )

                supporter_form = forms.SupporterForm(request.POST)
                if supporter_form.is_valid():
                    supporter = supporter_form.save(commit=True)
                    if supporter.band:
                        supporter.old_bands.add(supporter.band)
                    supporter.band = band
                    supporter.contacts.add(request.user)
                    supporter.save()
                    complete_text = utils.setting('complete_text')
                    notify.event_signup(
                        request,
                        supporter,
                    )

    template = 'consortial_billing/signup.html'

    context = {
        'band_form': band_form,
        'band': band,
        'supporter_form': supporter_form,
        'supporter': supporter,
        'signup_agreement': signup_agreement,
        'complete_text': complete_text,
    }

    return render(request, template, context)


def view_support_bands(request):
    display_bands = utils.get_display_bands()

    context = {
        'display_bands': display_bands,
    }

    template = 'consortial_billing/view_support_bands.html'

    return render(request, template, context)


def supporters(request):

    supporters = models.Supporter.objects.filter(
        active=True,
        display=True,
    )

    template = 'consortial_billing/supporters_press.html'

    context = {
        'supporters': supporters,
    }

    return render(request, template, context)


def view_custom_page(request, page_name):

    page = get_object_or_404(
        cms_models.Page,
        name=page_name,
        content_type=request.model_content_type,
        object_id=request.site_type.pk
    )

    currencies = models.Currency.objects.all()
    supporters = models.Supporter.objects.filter(
        active=True,
        display=True,
    )
    band_form = forms.BandForm()
    band = None

    if request.GET:
        if 'calculate' in request.GET:
            band_form = forms.BandForm(request.GET)
            if band_form.is_valid():
                band = band_form.save(commit=False)
                band_form = forms.BandForm(
                    instance=band,
                )

        elif 'start_signup' in request.GET:
            url = reverse('consortial_signup')
            params = request.GET.urlencode()
            return redirect(f'{url}?{params}')

    template = 'consortial_billing/custom.html'
    context = {
        'page': page,
        'supporters': supporters,
        'band_form': band_form,
        'band': band,
        'currencies': currencies,
    }

    return render(request, template, context)
