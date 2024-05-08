__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch
import decimal

from django.core.exceptions import ImproperlyConfigured

from plugins.consortial_billing import logic, models as supporter_models
from plugins.consortial_billing.tests import test_models
from utils.logger import get_logger

logic_logger = get_logger(logic.__name__)

CB = 'plugins.consortial_billing'


class LogicTests(test_models.TestCaseWithData):

    def test_get_display_bands(self):
        display_bands = logic.get_display_bands()
        self.assertEqual(
            display_bands[-1]['GBP'],
            1500,
        )

    @patch(f'{CB}.utils.open_saved_world_bank_data')
    def test_get_indicator_by_country(self, open_saved):

        open_saved.return_value = []
        data = logic.get_indicator_by_country(self.fake_indicator, 2050)
        open_saved.assert_called()
        self.assertEqual(data, {})

        open_saved.return_value = ['something', None]
        data = logic.get_indicator_by_country(self.fake_indicator, 2050)
        open_saved.assert_called()
        self.assertEqual(data, {})

        open_saved.return_value = [
            {},
            [
                {
                    'countryiso3code': 'NLD',
                    'value': 12345,
                }
            ]
        ]
        data = logic.get_indicator_by_country(self.fake_indicator, 2050)
        self.assertEqual(data['NLD'], 12345)

    def test_countries_with_billing_agents(self):
        self.assertEqual(
            {self.agent_gb.country},
            logic.countries_with_billing_agents(),
        )

    def test_get_base_band_standard_level(self):
        self.assertEqual(
            self.band_base_standard_de,
            logic.get_base_band(level=self.level_standard),
        )

    def test_get_base_band_other_level(self):
        self.assertEqual(
            self.band_base_silver_de,
            logic.get_base_band(level=self.level_silver),
        )

    def test_get_base_band_other_country(self):
        self.assertEqual(
            self.band_base_standard_gb,
            logic.get_base_band(country='GB'),
        )

    def test_get_base_band_no_args(self):
        self.assertEqual(
            self.band_base_standard_de,
            logic.get_base_band(),
        )

    def test_get_base_band_no_args_no_default_level(self):

        # Make it so there is no default level
        self.level_standard.default = False
        self.level_standard.save()

        base_band = logic.get_base_band()

        # Restore data
        self.level_standard.default = True
        self.level_standard.save()

        self.assertEqual(
            self.band_base_standard_de,
            base_band,
        )

    def test_get_base_bands(self):
        self.assertSetEqual(
            {
                self.band_base_standard_de,
                self.band_base_standard_gb,
                self.band_base_silver_de,
                self.band_base_silver_gb,
            },
            logic.get_base_bands(),
        )

    def test_get_base_band_for_level_falls_back(self):

        # Make it so the base band for one level is missing
        self.band_base_silver_de.category = 'special'
        self.band_base_silver_de.save()

        self.assertEqual(
            self.band_base_standard_de,
            logic.get_base_band(level=self.level_silver),
        )

        # Restore data
        self.band_base_silver_de.category = 'base'
        self.band_base_silver_de.save()

    def test_get_base_band_for_country_falls_back(self):

        # Make it so the base band for one country is missing
        self.band_base_standard_gb.category = 'special'
        self.band_base_standard_gb.save()

        self.assertEqual(
            self.band_base_standard_de,
            logic.get_base_band(country='GB'),
        )

        # Restore data
        self.band_base_standard_gb.category = 'base'
        self.band_base_standard_gb.save()

    @patch(f'{CB}.models.Band.objects.count')
    def test_get_base_band_with_no_bands_at_all(self, band_count):
        # In other words, the plugin is being
        # configured for the first time

        # Make it so there is no base band
        base_bands = supporter_models.Band.objects.filter(category='base')
        base_bands.update(category='special')

        band_count.return_value = 0
        base_band = logic.get_base_band()
        self.assertEqual(
            base_band,
            None,
        )

        # Restore data
        base_bands.update(category='base')

    def test_latest_multiplier_for_indicator(self):

        measure_key = 'dog'
        base_key = 'cat'
        warning_text = 'No dogs found!'
        with patch(
            'plugins.consortial_billing.logic.get_indicator_by_country',
        ) as get_indicator:
            get_indicator.return_value = {'dog': 5, 'cat': 10}
            multiplier, warning = logic.latest_multiplier_for_indicator(
                self.fake_indicator,
                measure_key,
                base_key,
                warning_text,
            )
            get_indicator.assert_called_once()
            self.assertEqual(multiplier, 0.5)
            self.assertEqual(warning, '')

            get_indicator.return_value = {'dog': 5}
            multiplier, warning = logic.latest_multiplier_for_indicator(
                self.fake_indicator,
                measure_key,
                base_key,
                warning_text,
            )
            self.assertEqual(multiplier, 1)
            self.assertEqual(warning, warning_text)

            get_indicator.return_value = {'cat': 10}
            multiplier, warning = logic.latest_multiplier_for_indicator(
                self.fake_indicator,
                measure_key,
                base_key,
                warning_text,
            )
            self.assertEqual(multiplier, 1)
            self.assertEqual(warning, warning_text)

    def test_latest_multiplier_for_indicator_during_initial_config(self):
        measure_key = 'dog'
        base_key = '---'
        warning_text = ''
        multiplier, warning = logic.latest_multiplier_for_indicator(
            self.fake_indicator,
            measure_key,
            base_key,
            warning_text,
        )
        self.assertEqual(multiplier, 1)
        self.assertEqual(warning, '')

    def test_get_settings_for_display(self):
        settings = logic.get_settings_for_display()
        setting_names = [setting.name for setting in settings]
        self.assertIn('complete_text', setting_names)

    def test_determine_billing_agent_default(self):
        agent = logic.determine_billing_agent(
            self.band_special_silver_fr_small.country
        )
        self.assertEqual(agent, self.agent_default)

    def test_determine_billing_agent_specific_country(self):
        agent = logic.determine_billing_agent(
            self.band_calc_standard_gb_large.country
        )
        self.assertEqual(agent, self.agent_gb)

    def test_keep_default_unique(self):

        self.assertTrue(self.level_standard.default)

        self.level_silver.default = True
        logic.keep_default_unique(self.level_silver)

        self.level_standard.refresh_from_db()
        self.assertFalse(self.level_standard.default)

        # Restore data
        self.level_standard.default = True
        self.level_standard.save()

    @patch(f'{CB}.models.Currency.exchange_rate')
    def test_get_total_revenue_no_args(self, exchange_rate):
        exchange_rate.return_value = (decimal.Decimal('1.000'), '')
        self.assertTupleEqual(
            (3500, self.currency_eur),
            logic.get_total_revenue(),
        )
        self.assertEqual(
            exchange_rate.call_count,
            4,
        )

    @patch(f'{CB}.models.Currency.exchange_rate')
    def test_get_total_revenue_in_currency(self, exchange_rate):
        exchange_rate.return_value = (decimal.Decimal('1.000'), '')
        self.assertTupleEqual(
            (3500, self.currency_gbp),
            logic.get_total_revenue(self.currency_gbp),
        )
        self.assertEqual(
            exchange_rate.call_count,
            4,
        )
