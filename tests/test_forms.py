__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from copy import copy
from datetime import timedelta
from django.core.exceptions import ValidationError

from unittest.mock import patch

from plugins.consortial_billing import forms
from plugins.consortial_billing.tests import test_models

CB = 'plugins.consortial_billing'


class FormTests(test_models.TestCaseWithData):

    def test_band_form_save_empty(self):
        band_form = forms.BandForm()
        with self.assertRaises(ValidationError):
            band_form.save(commit=False)

    @patch(f'{CB}.models.Band.calculate_fee')
    @patch(f'{CB}.logic.determine_billing_agent')
    def test_band_form_save_with_data_no_commit(self, det_agent, calc_fee):
        det_agent.return_value = self.agent_other
        calc_fee.return_value = (1000, 'Oh no!')
        data = {
            'country': 'BE',
            'currency': self.currency_other,
            'size': self.size_other,
            'level': self.level_other,
        }
        band_form = forms.BandForm(data)
        band = band_form.save(commit=False)
        calc_fee.assert_called()
        det_agent.assert_called()
        self.assertEqual(band.billing_agent, self.agent_other)
        self.assertEqual(band.fee, 1000)
        self.assertEqual(band.warnings, 'Oh no!')

    @patch(f'{CB}.models.Band.calculate_fee')
    @patch(f'{CB}.logic.determine_billing_agent')
    def test_band_form_save_fixed_fee_band(self, det_agent, calc_fee):
        det_agent.return_value = self.agent_other
        calc_fee.return_value = (7777, '')
        data = {
            'country': 'FR',
            'currency': self.currency_other,
            'size': self.size_other,
            'level': self.level_other,
        }
        band_form = forms.BandForm(data)
        band = band_form.save(commit=False)
        self.assertEqual(band.pk, self.band_fixed_fee.pk)

    @patch(f'{CB}.models.Band.calculate_fee')
    @patch(f'{CB}.logic.determine_billing_agent')
    def test_band_form_save_existing_band_commit(self, det_agent, calc_fee):
        det_agent.return_value = self.agent_other
        calc_fee.return_value = (2000, 'Oh no!')
        data = {
            'country': 'BE',
            'currency': self.currency_other,
            'size': self.size_other,
            'level': self.level_other,
        }
        band_form = forms.BandForm(data)
        band = band_form.save(commit=True)
        self.assertEqual(band.pk, self.band_other_two.pk)

    @patch(f'{CB}.models.Band.calculate_fee')
    @patch(f'{CB}.logic.determine_billing_agent')
    def test_band_form_save_new_band_commit(self, det_agent, calc_fee):
        det_agent.return_value = self.agent_default
        calc_fee.return_value = (500, '')
        data = {
            'country': 'DE',
            'currency': self.currency_other,
            'size': self.size_base,
            'level': self.level_base,
        }
        band_form = forms.BandForm(data)
        band = band_form.save(commit=True)
        self.assertNotIn(
            band.pk,
            [
                self.band_base.pk,
                self.band_other_one.pk,
                self.band_other_two.pk,
                self.band_other_three.pk,
            ]
        )
        band.delete()

    @patch(f'{CB}.models.Band.calculate_fee')
    @patch(f'{CB}.logic.determine_billing_agent')
    def test_band_form_save_handles_duplicates(self, det_agent, calc_fee):
        det_agent.return_value = self.agent_other
        calc_fee.return_value = (2000, 'Oh no!')
        duplicate_band = copy(self.band_other_two)
        duplicate_band.pk = None
        duplicate_band.datetime -= timedelta(hours=1)
        duplicate_band.save()

        data = {
            'country': 'BE',
            'currency': self.currency_other,
            'size': self.size_other,
            'level': self.level_other,
        }
        band_form = forms.BandForm(data)
        band = band_form.save()
        self.assertEqual(band.pk, self.band_other_two.pk)

        duplicate_band.delete()
