__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch, Mock, PropertyMock

from plugins.consortial_billing import utils
from plugins.consortial_billing.tests import test_models

CB = 'plugins.consortial_billing'


class UtilsTests(test_models.TestCaseWithData):

    def test_form_world_bank_url(self):
        url = utils.form_world_bank_url(self.fake_indicator, '2023')
        self.assertEqual(
            url,
            'https://api.worldbank.org/v2/country/all/indicator/'
            f'{self.fake_indicator}?date=2023&format=json&per_page=500',
        )

    def test_save_and_open_use_same_label(self):
        with patch(
            'plugins.consortial_billing.utils.save_media_file'
        ) as save_label:
            with patch('cms.models.MediaFile.objects.get') as get_label:
                with patch('json.loads'):
                    utils.save_file_for_indicator_and_year(
                        self.fake_indicator,
                        2023,
                        '',
                    )
                    utils.open_saved_world_bank_data(
                        self.fake_indicator,
                        2023,
                    )
                    saved_as = save_label.call_args.args[0]
                    opened_as = get_label.call_args.kwargs['label']
                    self.assertEqual(saved_as, opened_as)

    def test_fetch_world_bank_data_200(self):
        with patch(
            'plugins.consortial_billing.utils.save_file_for_indicator_and_year'
        ) as save_file:
            with patch('requests.get') as mock_get:
                response = Mock()
                type(response).status_code = PropertyMock(return_value=200)
                mock_get.return_value = response
                status_code = utils.fetch_world_bank_data(
                    self.fake_indicator,
                    2023,
                )
                save_file.assert_called()
                self.assertEqual(status_code, 200)

    def test_fetch_world_bank_data_404(self):
        with patch(
            'plugins.consortial_billing.utils.save_file_for_indicator_and_year'
        ) as save_file:
            with patch('requests.get') as mock_get:
                response = Mock()
                type(response).status_code = PropertyMock(return_value=404)
                mock_get.return_value = response
                status_code = utils.fetch_world_bank_data(
                    self.fake_indicator,
                    2023,
                )
                save_file.assert_not_called()
                self.assertEqual(status_code, 404)

    def test_generate_new_demo_data(self):
        with patch(
            'plugins.consortial_billing.logic.latest_multiplier_for_indicator',
            return_value=(0.85, ''),
        ):
            data = utils.generate_new_demo_data()
            self.assertEqual(
                data['thead'][0],
                'Standard'
            )
            small = data['tbody']['Small (0-4,999 students)']
            self.assertEqual(
                small['UK']['Higher']['currency'],
                '£'
            )
            large = data['tbody']['Large (10,000+ students)']
            self.assertGreater(
                large['USA']['Standard']['fee'],
                0
            )

    @patch(f'{CB}.utils.save_media_file')
    @patch(f'{CB}.utils.generate_new_demo_data')
    def test_update_demo_band_data(self, generate_new, save_media_file):
        generate_new.return_value = {}
        utils.update_demo_band_data()
        generate_new.assert_called()
        save_media_file.assert_called()

    @patch('json.loads')
    @patch('cms.models.MediaFile.objects.get')
    def test_get_saved_demo_band_data(self, media_get, json_loads):
        utils.get_saved_demo_band_data()
        media_get.assert_called()
        json_loads.assert_called()
