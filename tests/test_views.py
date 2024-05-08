__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import decimal
from unittest.mock import patch

from django.http import QueryDict
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

from plugins.consortial_billing import views, plugin_settings
from plugins.consortial_billing.tests import test_models
from core import include_urls  # imported so that urls will load


class ViewTests(test_models.TestCaseWithData):

    @patch('plugins.consortial_billing.logic.latest_multiplier_for_indicator')
    def test_manager_loads(self, latest_multiplier):
        latest_multiplier.return_value = (decimal.Decimal('1.000'), '')
        self.client.force_login(self.user_staff)
        response = self.client.get(
            reverse('supporters_manager'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'consortial_billing/manager.html')

    @patch('plugins.consortial_billing.logic.get_base_band')
    def test_manager_loads_with_no_base_band(self, get_base):
        get_base.return_value = None
        self.client.force_login(self.user_staff)
        response = self.client.get(
            reverse('supporters_manager'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'consortial_billing/manager.html')

    @patch('plugins.consortial_billing.logic.latest_multiplier_for_indicator')
    def test_manager_context_essential(self, latest_multiplier):
        latest_multiplier.return_value = (decimal.Decimal('1.000'), '')
        self.client.force_login(self.user_staff)
        response = self.client.get(
            reverse('supporters_manager'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(
            plugin_settings.SHORT_NAME,
            response.context['plugin'],
        )
        self.assertSetEqual(
            {
                self.band_base_standard_de,
                self.band_base_standard_gb,
                self.band_base_silver_de,
                self.band_base_silver_gb,
            },
            response.context['base_bands'],
        )
        self.assertEqual(
            plugin_settings,
            response.context['plugin_settings'],
        )

    @patch('plugins.consortial_billing.logic.latest_multiplier_for_indicator')
    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.views.call_command')
    def test_manager_post_fetch_data(self, call_command, render, latest_multiplier):
        latest_multiplier.return_value = (decimal.Decimal('1.000'), '')
        type(self.request).user = self.user_staff
        type(self.request).POST = {'fetch_data': None}
        views.manager(self.request)
        call_command.assert_called()

    def test_signup_loads(self):
        self.client.force_login(self.user_supporter)
        response = self.client.get(
            reverse('supporter_signup'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'consortial_billing/signup.html')
        self.assertTrue(response.context['signup_agreement'])

    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.forms.BandForm.save')
    def test_signup_get_with_params(self, band_save, render):
        type(self.request).user = self.user_supporter
        type(self.request).GET = {
            'country': 'NL',
            'size': self.size_large.pk,
            'level': self.level_standard.pk,
            'currency': self.currency_eur.pk,
            'category': 'calculated',
            'start_signup': '',
        }
        views.signup(self.request)
        band_save.assert_called_once_with(commit=False)

    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.forms.BandForm.save')
    def test_signup_post_calculate(self, band_save, render):
        type(self.request).user = self.user_supporter
        type(self.request).POST = {
            'country': 'NL',
            'size': self.size_large.pk,
            'level': self.level_standard.pk,
            'currency': self.currency_eur.pk,
            'category': 'calculated',
            'calculate': '',
            'name': 'RKD',
        }
        views.signup(self.request)
        band_save.assert_called_once_with(commit=False)
        context = render.call_args.args[2]
        context['supporter_form'].full_clean()
        self.assertEqual(
            context['supporter_form'].cleaned_data['name'],
            'RKD',
        )

    @patch('plugins.consortial_billing.notifications.notify.event_signup')
    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.forms.BandForm.save')
    @patch('plugins.consortial_billing.forms.SupporterSignupForm.save')
    def test_signup_post_sign_up_complete(
        self,
        supporter_save,
        band_save,
        render,
        event_signup,
    ):
        type(self.request).user = self.user_supporter
        type(self.request).POST = {
            'country': 'BE',
            'size': self.size_small.pk,
            'level': self.level_silver.pk,
            'currency': self.currency_eur.pk,
            'category': 'calculated',
            'sign_up': '',
            'name': self.supporter_antwerp.name,
        }
        band_save.return_value = self.band_calc_silver_be_small
        supporter_save.return_value = self.supporter_antwerp
        views.signup(self.request)
        band_save.assert_called_once_with(commit=True)
        supporter_save.assert_called_once_with(
            commit=True,
            band=band_save.return_value,
        )
        context = render.call_args.args[2]
        self.assertTrue(context['complete_text'])
        self.assertFalse(context['redirect_text'])
        event_signup.assert_called_once_with(
            self.request,
            self.supporter_antwerp,
        )

    @patch('plugins.consortial_billing.notifications.notify.event_signup')
    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.forms.BandForm.save')
    @patch('plugins.consortial_billing.forms.SupporterSignupForm.save')
    def test_signup_post_sign_up_redirect(
        self,
        supporter_save,
        band_save,
        render,
        event_signup,
    ):
        type(self.request).user = self.user_supporter
        type(self.request).POST = {
            'country': 'GB',
            'size': self.size_large.pk,
            'level': self.level_standard.pk,
            'currency': self.currency_gbp.pk,
            'category': 'calculated',
            'sign_up': '',
            'name': self.supporter_bbk.name,
        }
        band_save.return_value = self.band_calc_standard_gb_large
        supporter_save.return_value = self.supporter_bbk
        views.signup(self.request)
        context = render.call_args.args[2]
        self.assertTrue(context['redirect_text'])
        self.assertFalse(context['complete_text'])

    def test_public_supporter_list_loads(self):
        response = self.client.get(
            reverse('public_supporter_list'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'consortial_billing/supporters_press.html',
        )

    def test_view_custom_page_loads(self):
        url = reverse('supporters_custom_page', args=[self.custom_page.name])
        response = self.client.get(
            url,
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'consortial_billing/custom.html',
        )

    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.views.redirect')
    def test_view_custom_page_get_start_signup(self, redirect, render):
        type(self.request).user = self.user_supporter
        type(self.request).GET = QueryDict(mutable=True)
        type(self.request).GET.update(
            {
                'start_signup': '',
            }
        )
        views.view_custom_page(self.request, self.custom_page.name)
        url = reverse('supporter_signup')
        redirect.assert_called_once_with(url+'?start_signup=')
