__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch, Mock
import decimal

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest

from plugins.consortial_billing import models, plugin_settings
from plugins.consortial_billing import utils
from utils.testing import helpers
from press import models as press_models
from cms.models import Page


class TestCaseWithData(TestCase):

    @classmethod
    def setUpTestData(cls):
        plugin_settings.install(fetch_data=False)
        cls.press = press_models.Press(domain="supporters.org")
        cls.press.save()
        cls.user_supporter = helpers.create_user('user_supporter@example.org')
        cls.user_supporter.is_active = True
        cls.user_supporter.save()
        cls.user_staff = helpers.create_user('user_billing_staff@example.org')
        cls.user_staff.is_staff = True
        cls.user_staff.is_active = True
        cls.user_staff.save()
        cls.user_agent = helpers.create_user('user_agent@example.org')
        cls.user_agent.is_active = True
        cls.user_agent.save()
        cls.agent_default = models.BillingAgent.objects.create(
            name='Open Library of Humanities',
            default=True,
        )
        cls.agent_default.save()
        models.AgentContact.objects.get_or_create(
            agent=cls.agent_default,
            account=cls.user_staff,
        )
        cls.agent_gb = models.BillingAgent.objects.create(
            name='Diamond OA Association',
            country='GB',
            redirect_url='example.org'
        )
        cls.agent_gb.save()
        models.AgentContact.objects.get_or_create(
            agent=cls.agent_gb,
            account=cls.user_agent,
        )
        cls.size_large = models.SupporterSize.objects.create(
            name='Large',
            description='10,000+ students',
            multiplier=1,
        )
        cls.size_small = models.SupporterSize.objects.create(
            name='Small',
            description='0-4,999 students',
            multiplier=0.6,
        )
        cls.level_standard = models.SupportLevel.objects.create(
            name='Standard',
            order=2,
            default=True,
        )
        cls.level_silver = models.SupportLevel.objects.create(
            name='Silver',
            order=1,
        )
        cls.currency_eur = models.Currency.objects.create(
            code='EUR',
            region='EMU',
            symbol='€',
        )
        cls.currency_gbp = models.Currency.objects.create(
            code='GBP',
            region='GBR',
            symbol='£',
        )
        cls.band_base_silver_de = models.Band.objects.create(
            level=cls.level_silver,
            country='DE',
            size=cls.size_large,
            currency=cls.currency_eur,
            billing_agent=cls.agent_default,
            fee=5000,
            category='base',
        )
        cls.band_base_standard_de = models.Band.objects.create(
            level=cls.level_standard,
            country='DE',
            size=cls.size_large,
            currency=cls.currency_eur,
            billing_agent=cls.agent_default,
            fee=1000,
            category='base',
        )
        cls.band_base_silver_gb = models.Band.objects.create(
            level=cls.level_silver,
            country='GB',
            size=cls.size_large,
            currency=cls.currency_gbp,
            billing_agent=cls.agent_gb,
            fee=4000,
            category='base',
        )
        cls.band_base_standard_gb = models.Band.objects.create(
            level=cls.level_standard,
            country='GB',
            size=cls.size_large,
            currency=cls.currency_gbp,
            billing_agent=cls.agent_gb,
            fee=2000,
            category='base',
        )
        cls.band_calc_silver_gb_large = models.Band.objects.create(
            level=cls.level_silver,
            country='GB',
            size=cls.size_large,
            currency=cls.currency_gbp,
            billing_agent=cls.agent_gb,
            fee=4000,
            warnings='',
            category='calculated',
        )
        cls.band_calc_silver_be_small = models.Band.objects.create(
            level=cls.level_silver,
            country='BE',
            size=cls.size_small,
            currency=cls.currency_eur,
            billing_agent=cls.agent_default,
            fee=2000,
            warnings='',
            category='calculated',
        )
        cls.band_calc_standard_gb_large = models.Band.objects.create(
            level=cls.level_standard,
            country='GB',
            size=cls.size_large,
            currency=cls.currency_gbp,
            billing_agent=cls.agent_gb,
            fee=1500,
            warnings='',
            category='calculated',
        )
        cls.band_special_silver_fr_small = models.Band.objects.create(
            level=cls.level_silver,
            size=cls.size_small,
            country='FR',
            currency=cls.currency_eur,
            billing_agent=cls.agent_default,
            fee=7777,
            warnings='',
            category='special',
        )
        cls.supporter_bbk = models.Supporter.objects.create(
            name='Birkbeck, University of London',
            ror='https://ror.org/02mb95055',
            band=cls.band_calc_standard_gb_large,
            active=True,
        )
        cls.supporter_bbk.save()
        models.SupporterContact.objects.get_or_create(
            supporter=cls.supporter_bbk,
            account=cls.user_supporter,
        )
        cls.supporter_antwerp = models.Supporter.objects.create(
            name='University of Antwerp',
            band=cls.band_calc_silver_be_small,
            active=True,
        )
        cls.supporter_antwerp.save()
        models.SupporterContact.objects.get_or_create(
            supporter=cls.supporter_antwerp,
            account=cls.user_supporter,
        )
        cls.fake_indicator = 'ABC.DEF.GHI'
        cls.custom_page = Page.objects.create(
            content_type=ContentType.objects.get_for_model(cls.press),
            object_id=cls.press.pk,
            name='become-a-supporter',
            display_name='Become a Supporter',
        )

    def setUp(self):
        self.request = Mock(HttpRequest)
        type(self.request).GET = {}
        type(self.request).POST = {}
        type(self.request).journal = None
        type(self.request).press = Mock(press_models.Press)
        press_type = ContentType.objects.get_for_model(self.press)
        type(self.request).model_content_type = press_type
        type(self.request).site_type = self.press


class ModelTests(TestCaseWithData):

    def test_billing_agent_save(self):

        # Set up test conditions
        self.agent_gb.default = True
        self.agent_gb.save()
        self.agent_default.refresh_from_db()
        self.agent_gb.refresh_from_db()

        # Get test values
        other_has_country = bool(self.agent_gb.country)
        default_still_default = self.agent_default.default

        # Restore test data
        self.agent_default.default = True
        self.agent_default.save()
        self.agent_gb.country = 'GB'
        self.agent_gb.save()

        # Run test
        self.assertFalse(other_has_country)
        self.assertFalse(default_still_default)

    @patch('plugins.consortial_billing.logic.latest_multiplier_for_indicator')
    def test_currency_exchange_rate_with_typical_args(self, latest_multiplier):
        self.currency_eur.exchange_rate(base_band=self.band_base_standard_gb)
        expected_args = (
            plugin_settings.RATE_INDICATOR,
            self.currency_eur.region,  # Target currency
            self.currency_gbp.region, # Specified base currency
            utils.setting('missing_data_exchange_rate')
        )
        self.assertTupleEqual(
            expected_args,
            latest_multiplier.call_args.args,
        )

    @patch('plugins.consortial_billing.logic.latest_multiplier_for_indicator')
    def test_currency_exchange_rate_with_no_args(self, latest_multiplier):
        self.currency_gbp.exchange_rate()
        expected_args = (
            plugin_settings.RATE_INDICATOR,
            self.currency_gbp.region,  # Target currency
            self.currency_eur.region, # Default base currency
            utils.setting('missing_data_exchange_rate')
        )
        self.assertTupleEqual(
            expected_args,
            latest_multiplier.call_args.args,
        )

    @patch('plugins.consortial_billing.logic.latest_multiplier_for_indicator')
    def test_band_economic_disparity(self, latest_multiplier):
        self.band_special_silver_fr_small.economic_disparity
        expected_args = (
            plugin_settings.DISPARITY_INDICATOR,
            self.band_special_silver_fr_small.country.alpha3, # Target country
            self.band_base_silver_de.country.alpha3, # Default base country
            utils.setting('missing_data_economic_disparity')
        )
        self.assertTupleEqual(
            expected_args,
            latest_multiplier.call_args.args,
        )

    def test_band_calculate_fee(self):
        with patch(
            'plugins.consortial_billing.logic.latest_multiplier_for_indicator',
            return_value=(decimal.Decimal(0.85), ''),
        ) as latest_multiplier:
            fee, _ = self.band_calc_standard_gb_large.calculate_fee()
            expected_fee = round(
                2000                      # base
                # * decimal.Decimal(0.6)  # size does not matter for higher level
                * decimal.Decimal(0.85)   # Patched GNI
                * decimal.Decimal(0.85),  # Patched exchange rate
                -1
            )
            latest_multiplier.assert_called()
            self.assertEqual(fee, expected_fee)

    def test_band_determine_billing_agent_default(self):
        agent = self.band_special_silver_fr_small.determine_billing_agent()
        self.assertEqual(agent, self.agent_default)

    def test_band_determine_billing_agent_specific_country(self):
        agent = self.band_base_standard_gb.determine_billing_agent()
        self.assertEqual(agent, self.agent_gb)

    def test_band_save_calculated(self):
        with patch.object(
            self.band_calc_standard_gb_large,
            'calculate_fee',
            return_value=(1111, '')
        ) as calculate_fee:
            self.band_calc_standard_gb_large.fee = None
            self.band_calc_standard_gb_large.save()
            calculate_fee.assert_called_once()

    def test_band_save_special_formerly_calculated(self):
        # Set up data
        self.band_calc_standard_gb_large.category = 'special'
        new_band = self.band_calc_standard_gb_large.save()

        # Restore instances
        self.band_calc_standard_gb_large.category = 'calculated'
        self.band_calc_standard_gb_large.save()

        # Run test
        self.assertNotEqual(
            self.band_calc_standard_gb_large,
            new_band,
        )
