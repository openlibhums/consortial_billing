__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch

from django.http import QueryDict
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

from plugins.consortial_billing import views, plugin_settings
from plugins.consortial_billing.tests import test_models
from core import include_urls  # imported so that urls will load


class ViewTests(test_models.TestCaseWithData):

    def test_manager_loads(self):
        self.client.force_login(self.user_staff)
        response = self.client.get(
            reverse('supporters_manager'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'consortial_billing/manager.html')

    @patch('plugins.consortial_billing.logic.get_base_band')
    def test_manager_loads_with_no_base_band(self, get_base):
        get_base.side_effect = ImproperlyConfigured('No base')
        self.client.force_login(self.user_staff)
        response = self.client.get(
            reverse('supporters_manager'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'consortial_billing/manager.html')

    def test_manager_context_essential(self):
        self.client.force_login(self.user_staff)
        response = self.client.get(
            reverse('supporters_manager'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(
            plugin_settings.SHORT_NAME,
            response.context['plugin'],
        )
        self.assertEqual(
            self.band_base,
            response.context['base_band'],
        )
        self.assertEqual(
            plugin_settings,
            response.context['plugin_settings'],
        )

    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.views.call_command')
    def test_manager_post_fetch_data(self, call_command, render):
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
            'size': self.size_other.pk,
            'level': self.level_other.pk,
            'currency': self.currency_other.pk,
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
            'size': self.size_other.pk,
            'level': self.level_other.pk,
            'currency': self.currency_other.pk,
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
    @patch('plugins.consortial_billing.forms.SupporterForm.save')
    def test_signup_post_sign_up_complete(
        self,
        supporter_save,
        band_save,
        render,
        event_signup,
    ):
        type(self.request).user = self.user_supporter
        type(self.request).POST = {
            'country': 'GB',
            'size': self.size_other.pk,
            'level': self.level_other.pk,
            'currency': self.currency_base.pk,
            'sign_up': '',
            'name': 'University of Essex',
        }
        band_save.return_value = self.band_other_three
        supporter_save.return_value = self.supporter_two
        views.signup(self.request)
        band_save.assert_called_once_with(commit=True)
        supporter_save.assert_called_once_with(commit=True)
        context = render.call_args.args[2]
        self.assertTrue(context['complete_text'])
        self.assertFalse(context['redirect_text'])
        event_signup.assert_called_once_with(
            self.request,
            self.supporter_two,
        )

    @patch('plugins.consortial_billing.notifications.notify.event_signup')
    @patch('plugins.consortial_billing.views.render')
    @patch('plugins.consortial_billing.forms.BandForm.save')
    @patch('plugins.consortial_billing.forms.SupporterForm.save')
    def test_signup_post_sign_up_redirect(
        self,
        supporter_save,
        band_save,
        render,
        event_signup,
    ):
        type(self.request).user = self.user_supporter
        type(self.request).POST = {
            'country': 'BE',
            'size': self.size_other.pk,
            'level': self.level_other.pk,
            'currency': self.currency_other.pk,
            'sign_up': '',
            'name': 'University of Antwerp',
        }
        band_save.return_value = self.band_other_two
        supporter_save.return_value = self.supporter_four
        views.signup(self.request)
        context = render.call_args.args[2]
        self.assertTrue(context['redirect_text'])
        self.assertFalse(context['complete_text'])

    def test_view_support_bands_loads(self):

        # This login is only needed
        # during beta testing while the page has a
        # staff_member_required check
        self.client.force_login(self.user_staff)

        response = self.client.get(
            reverse('view_support_bands'),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'consortial_billing/view_support_bands.html',
        )

    def test_supporters_loads(self):
        response = self.client.get(
            reverse('supporters_list'),
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
    @patch('plugins.consortial_billing.forms.BandForm.save')
    def test_view_custom_page_get_calculate(self, band_save, render):
        type(self.request).user = self.user_supporter
        type(self.request).GET = {
            'country': 'NL',
            'size': self.size_other.pk,
            'level': self.level_other.pk,
            'currency': self.currency_other.pk,
            'calculate': '',
        }
        views.view_custom_page(self.request, self.custom_page.name)
        band_save.assert_called_once_with(commit=False)

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
