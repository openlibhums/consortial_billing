import decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator

from plugins.consortial_billing import utils, \
     logic, models as supporter_models, plugin_settings, forms
from plugins.consortial_billing.notifications import notify

from core.views import GenericFacetedListView
from core.models import Account
from core.model_utils import search_model_admin
from cms import models as cms_models
from utils.logger import get_logger
from security.decorators import base_check_required

logger = get_logger(__name__)


@staff_member_required
def manager(request):

    if request.POST:
        if 'fetch_data' in request.POST:
            indicator = request.POST.get('fetch_data', None)
            call_command('fetch_world_bank_data', indicator)

        elif 'update_demo' in request.POST:
            call_command('update_demo_band_data')

    base_bands = logic.get_base_bands()

    latest_gni_data = logic.latest_dataset_for_indicator(
        plugin_settings.DISPARITY_INDICATOR,
    )
    latest_exchange_rate_data = logic.latest_dataset_for_indicator(
        plugin_settings.RATE_INDICATOR,
    )
    latest_demo_data = logic.latest_dataset_for_indicator(
        utils.DEMO_DATA_FILENAME,
    )
    settings = logic.get_settings_for_display()
    currencies = []
    for curr in supporter_models.Currency.objects.all():
        rate, _warning = curr.exchange_rate()
        rate = rate.quantize(decimal.Decimal('1.000'))
        currencies.append((rate, curr.code))

    context = {
        'plugin': plugin_settings.SHORT_NAME,
        'supporters': supporter_models.Supporter.objects.all(),
        'agents': supporter_models.BillingAgent.objects.all(),
        'sizes': supporter_models.SupporterSize.objects.all(),
        'levels': supporter_models.SupportLevel.objects.all(),
        'currencies': currencies,
        'base_bands': base_bands,
        'latest_gni_data': latest_gni_data,
        'latest_exchange_rate_data': latest_exchange_rate_data,
        'latest_demo_data': latest_demo_data,
        'settings': settings,
        'plugin_settings': plugin_settings,
    }

    template = 'consortial_billing/manager.html'

    return render(request, template, context)


@base_check_required
def signup(request):

    band_form = forms.BandForm()
    band = None
    supporter_form = forms.SupporterSignupForm()
    supporter = None
    signup_agreement = utils.setting('signup_agreement')
    redirect_text = ''
    complete_text = ''

    # This handles the redirect from custom CMS pages with a GET
    # calculation form
    if request.GET:
        if 'start_signup' in request.GET:
            band_form = forms.BandForm(request.GET)
            if band_form.is_valid():
                band = band_form.save(commit=False)
                band_form = forms.BandForm(
                    instance=band,
                )

    if request.POST:
        if 'calculate' in request.POST:
            band_form = forms.BandForm(request.POST)
            if band_form.is_valid():
                band = band_form.save(commit=False)
                band_form = forms.BandForm(
                    instance=band,
                )

                supporter_form = forms.SupporterSignupForm(request.POST)

        if 'sign_up' in request.POST:
            band_form = forms.BandForm(request.POST)
            if band_form.is_valid():
                band = band_form.save(commit=True)
                band_form = forms.BandForm(
                    instance=band,
                )

                supporter_form = forms.SupporterSignupForm(request.POST)
                if supporter_form.is_valid():
                    supporter = supporter_form.save(commit=False)
                    supporter.band = band
                    supporter.save()
                    supporter_models.SupporterContact.objects.get_or_create(
                        supporter=supporter,
                        account=request.user
                    )
                    if band.billing_agent.redirect_url:
                        redirect_text = utils.setting('redirect_text')
                    else:
                        complete_text = utils.setting('complete_text')
                    notify.event_signup(
                        request,
                        supporter,
                    )

    context = {
        'band_form': band_form,
        'band': band,
        'supporter_form': supporter_form,
        'supporter': supporter,
        'signup_agreement': signup_agreement,
        'redirect_text': redirect_text,
        'complete_text': complete_text,
    }

    if request.press.theme == 'hourglass':
        template = 'custom/supporter-signup.html'
    else:
        template = 'consortial_billing/signup.html'

    return render(request, template, context)


def supporters(request):

    supporters = supporter_models.Supporter.objects.filter(
        active=True,
        display=True,
    ).order_by(
        'band__country', 'name'
    )

    if request.press.theme == 'hourglass':
        template = 'custom/supporters.html'
    else:
        template = 'consortial_billing/supporters_press.html'

    context = {
        'supporters': supporters,
    }

    return render(request, template, context)


def view_custom_page(request, page_name):

    if request.GET and 'start_signup' in request.GET:
        url = reverse('supporter_signup')
        params = request.GET.urlencode()
        return redirect(f'{url}?{params}')

    page = get_object_or_404(
        cms_models.Page,
        name=page_name,
        content_type=request.model_content_type,
        object_id=request.site_type.pk
    )

    if page.template:
        template = page.template
    else:
        template = 'consortial_billing/custom.html'
    context = {
        'page': page,
    }

    return render(request, template, context)


@method_decorator(staff_member_required, name='dispatch')
class SupporterList(GenericFacetedListView):

    model = supporter_models.Supporter
    template_name = 'consortial_billing/supporter_list.html'

    def get_facets(self):

        band_obj = supporter_models.Band.objects.filter(
            current_supporter__pk=OuterRef('pk'),
        )

        band_category = Subquery(
            band_obj.values('category')[:1]
        )

        return {
            'q': {
                'type': 'search',
                'field_label': 'Search',
            },
            'active': {
                'type': 'boolean',
                'field_label': 'Active',
            },
            'band_category': {
                'type': 'charfield_with_choices',
                'annotations': {
                    'band_category': band_category,
                },
                'model_choices': supporter_models.Band._meta.get_field('category').choices,
                'field_label': 'Band category',
            },
            'band__datetime__date__gte': {
                'type': 'date',
                'field_label': 'Band updated after',
            },
            'band__datetime__date__lt': {
                'type': 'date',
                'field_label': 'Band updated before',
            },
            'band__fee__gt': {
                'type': 'integer',
                'field_label': 'Fee greater than',
            },
            'band__fee__lt': {
                'type': 'integer',
                'field_label': 'Fee less than',
            },
            'band__currency': {
                'type': 'foreign_key',
                'model': supporter_models.Currency,
                'field_label': 'Currency',
                'choice_label_field': 'code',
            },
            'band__level': {
                'type': 'foreign_key',
                'model': supporter_models.SupportLevel,
                'field_label': 'Support level',
                'choice_label_field': 'name',
            },
            'band__size': {
                'type': 'foreign_key',
                'model': supporter_models.SupporterSize,
                'field_label': 'Institution size',
                'choice_label_field': 'name',
            },
        }

    def get_order_by_choices(self):
        return [
            ('name', 'Names A-Z'),
            ('-name', 'Names Z-A'),
            ('-band__datetime', 'Modified recently'),
            ('band__datetime', 'Not modified recently'),
            ('-band__fee', 'Highest fee'),
            ('band__fee', 'Lowest fee'),
        ]

    def get_order_by(self):
        order_by = self.request.GET.get('order_by', 'name')
        order_by_choices = self.get_order_by_choices()
        return order_by if order_by in dict(order_by_choices) else ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@staff_member_required
def edit_supporter_band(request, supporter_id=None):

    supporter = None
    band = None
    add_band = False
    if supporter_id:
        supporter = supporter_models.Supporter.objects.get(pk=supporter_id)
        band = supporter.band
    supporter_form = forms.EditSupporterForm(instance=supporter)
    band_form = forms.EditBandForm(instance=band)
    user_search_form = forms.AccountAdminSearchForm()
    user_search_results = []
    next_url = request.GET.get('next')

    if request.method == 'POST':
        supporter_form = forms.EditSupporterForm(
            request.POST,
            instance=supporter,
        )
        band_form = forms.EditBandForm(
            request.POST,
            instance=band,
        )

        if 'autofill_ror' in request.POST:
            # If a user enters an invalid ROR manually,
            # and then they press the Autofill button,
            # we want to check the API and autofill the form
            # with a matching ROR,
            # before the rest of the form data is validated.
            ror = supporter.get_ror(name=request.POST['name'])
            if ror:
                post_data = request.POST.copy()
                post_data.update({'ror': ror})
                supporter_form = forms.EditSupporterForm(
                    post_data,
                    instance=supporter,
                )
                if ror == supporter.ror:
                    message = f'Existing ROR confirmed: { ror }.'
                else:
                    message = f'Autofilled new ROR: { ror }.'
                messages.add_message(request, messages.SUCCESS, message)
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    f'ROR could not be autofilled.'
                )

        if supporter_form.is_valid():
            supporter = supporter_form.save(commit=not(band_form.is_valid()))
            if band_form.is_valid():
                band = band_form.save()
                supporter.band = band
                supporter.save()

            if 'save_continue' in request.POST or 'save_return' in request.POST:
                message = f'{ supporter.name } details saved.'
                messages.add_message(request, messages.SUCCESS, message)
                if band_form.is_valid():
                    message = f'Band { band.pk } saved:\n { band }.'
                    messages.add_message(request, messages.SUCCESS, message)
                elif band:
                    message = 'Something went wrong. Please try again.'
                    messages.add_message(request, messages.WARNING, message)
            elif 'remove_contact' in request.POST:
                contact = supporter_models.SupporterContact.objects.get(
                    pk=request.POST.get('remove_contact')
                )
                message = f'Contact removed: { contact }.'
                contact.delete()
                messages.add_message(request, messages.SUCCESS, message)
            elif 'add_contact' in request.POST:
                account = Account.objects.get(pk=request.POST.get('add_contact'))
                contact, _created = supporter_models.SupporterContact.objects.get_or_create(
                    supporter=supporter,
                    account=account,
                )
                message = f'Contact added: { contact }.'
                messages.add_message(request, messages.SUCCESS, message)
            elif 'add_band' in request.POST:
                add_band = True
            elif 'save_continue' in request.POST:
                user_search_form = forms.AccountAdminSearchForm()
            elif 'save_return' in request.POST and next_url:
                return redirect(next_url)
            elif 'search_user' in request.POST or request.POST['q']:
                user_search_form = forms.AccountAdminSearchForm(request.POST)
                results, _dups = search_model_admin(request, Account)
                user_search_results = results.exclude(
                    supportercontact__supporter=supporter,
                )[:10]

            if not supporter_id:
                return redirect(
                    reverse(
                        'edit_supporter_band',
                        kwargs={'supporter_id': supporter.pk}
                    )
                )
        else:
            for form in [supporter_form, band_form]:
                for field, errors in form.errors.items():
                    label = form.fields[field].label
                    for error in errors:
                        messages.add_message(
                            request,
                            messages.WARNING,
                            f'{ label }: {error}',
                        )

        supporter_form = forms.EditSupporterForm(instance=supporter)
        band_form = forms.EditBandForm(instance=band)

    template = 'consortial_billing/edit_supporter_band.html'

    context = {
        'supporter': supporter,
        'supporter_form': supporter_form,
        'band': band,
        'add_band': add_band,
        'band_form': band_form,
        'next_url': next_url,
        'user_search_results': user_search_results,
        'user_search_form': user_search_form,
    }

    return render(request, template, context)


