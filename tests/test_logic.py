__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured

from plugins.consortial_billing import logic
from plugins.consortial_billing.tests import test_models
from utils.logger import get_logger

logic_logger = get_logger(logic.__name__)


class LogicTests(test_models.TestCaseWithData):

    def test_get_display_bands(self):
        display_bands = logic.get_display_bands()
        self.assertEqual(
            display_bands[-1]['GBP'],
            '1000&ndash;1001',
        )

    def test_get_indicator_by_country(self):
        with patch(
            'plugins.consortial_billing.utils.open_saved_world_bank_data',
        ) as open_saved:
            open_saved.return_value = [{}, []]
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

    def test_get_base_band(self):

        base_band = logic.get_base_band(self.level_base)
        self.assertEqual(
            self.band_base,
            base_band,
        )
        other_base_band = logic.get_base_band(self.level_other)
        self.assertEqual(
            self.band_base_level_other,
            other_base_band,
        )

    def test_get_base_bands(self):

        base_bands = logic.get_base_bands()
        self.assertListEqual(
            [
                self.band_base_country_other,
                self.band_base_level_other,
                self.band_base
            ],
            base_bands,
        )

    def test_get_base_band_for_level_falls_back(self):

        # Make it so the base band for one level is missing
        self.band_base_level_other.base = False
        self.band_base_level_other.save()

        base_band = logic.get_base_band(self.level_other)
        self.assertEqual(
            self.band_base,
            base_band,
        )

        # Restore data
        self.band_base_level_other.base = True
        self.band_base_level_other.save()

    @patch('plugins.consortial_billing.models.Band.objects.count')
    def test_get_base_band_with_no_bands_at_all(self, band_count):
        # In other words, the plugin is being
        # configured for the first time

        # Make it so there is no base band
        self.band_base.base = False
        self.band_base.save()
        self.band_base_level_other.base = False
        self.band_base_level_other.save()

        band_count.return_value = 0
        base_band = logic.get_base_band()
        self.assertEqual(
            base_band,
            None,
        )

        # Restore data
        self.band_base.base = True
        self.band_base.save()
        self.band_base_level_other.base = True
        self.band_base_level_other.save()

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
            with self.assertRaises(ImproperlyConfigured):
                multiplier, warning = logic.latest_multiplier_for_indicator(
                    self.fake_indicator,
                    measure_key,
                    base_key,
                    warning_text,
                )

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

    def test_keep_default_unique(self):

        self.assertTrue(self.level_base.default)

        self.level_other.default = True
        logic.keep_default_unique(self.level_other)

        self.level_base.refresh_from_db()
        self.assertFalse(self.level_base.default)

        # Restore data
        self.level_base.default = True
        self.level_base.save()
