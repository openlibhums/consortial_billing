__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.core.exceptions import ValidationError

from unittest.mock import patch

from plugins.consortial_billing import forms
from plugins.consortial_billing.tests import test_models


class FormTests(test_models.TestCaseWithData):

    def test_band_form_save_empty(self):
        band_form = forms.BandForm()
        with self.assertRaises(ValidationError):
            band_form.save(commit=False)

    def test_band_form_save_with_data_no_commit(self):
        with patch(
            'plugins.consortial_billing.models.Band.determine_billing_agent',
            return_value=self.agent_other,
        ) as determine_billing_agent:
            with patch(
                'plugins.consortial_billing.models.Band.calculate_fee',
                return_value=(1000, 'Oh no!'),
            ) as calculate_fee:
                data = {
                    'country': 'BE',
                    'currency': self.currency_other,
                    'size': self.size_other,
                    'level': self.level_other,
                }
                band_form = forms.BandForm(data)
                band = band_form.save(commit=False)
                calculate_fee.assert_called()
                determine_billing_agent.assert_called()
                self.assertEqual(
                    band.billing_agent,
                    self.agent_other,
                )
                self.assertEqual(
                    band.fee,
                    1000,
                )
                self.assertEqual(
                    band.warnings,
                    'Oh no!',
                )

    def test_band_form_save_fixed_fee_band(self):
        with patch(
            'plugins.consortial_billing.logic.determine_billing_agent',
            return_value=self.agent_other,
        ):
            data = {
                'country': 'FR',
                'currency': self.currency_other,
                'size': self.size_other,
                'level': self.level_other,
            }
            band_form = forms.BandForm(data)
            band = band_form.save(commit=False)
            self.assertEqual(band.pk, self.band_fixed_fee.pk)

    def test_band_form_save_existing_band_commit(self):
        with patch(
            'plugins.consortial_billing.models.Band.determine_billing_agent',
            return_value=self.agent_other,
        ):
            with patch(
                'plugins.consortial_billing.models.Band.calculate_fee',
                return_value=(2000, 'Oh no!'),
            ):
                data = {
                    'country': 'BE',
                    'currency': self.currency_other,
                    'size': self.size_other,
                    'level': self.level_other,
                }
                band_form = forms.BandForm(data)
                band = band_form.save(commit=True)
                self.assertEqual(band.pk, self.band_other_two.pk)

    def test_band_form_save_new_band_commit(self):
        with patch(
            'plugins.consortial_billing.models.Band.determine_billing_agent',
            return_value=self.agent_default,
        ):
            with patch(
                'plugins.consortial_billing.models.Band.calculate_fee',
                return_value=(500, ''),
            ):
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
