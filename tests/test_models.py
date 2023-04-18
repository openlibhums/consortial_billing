__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch, Mock

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest

from plugins.consortial_billing import models, plugin_settings
from utils.testing import helpers
from press import models as press_models
from cms.models import Page


class TestCaseWithData(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.agent_default, _c = models.BillingAgent.objects.get_or_create(
            name='Open Library of Humanities',
            default=True,
        )
        cls.agent_default.users.add(cls.user_staff)
        cls.agent_default.save()
        cls.agent_other, _c = models.BillingAgent.objects.get_or_create(
            name='Diamond OA Association',
            country='BE',
            redirect_url='example.org'
        )
        cls.agent_other.users.add(cls.user_agent)
        cls.agent_other.save()
        cls.size_base, _c = models.SupporterSize.objects.get_or_create(
            name='Large',
            description='10,000+ FTE',
            multiplier=1,
        )
        cls.size_other, _c = models.SupporterSize.objects.get_or_create(
            name='Small',
            description='0-4,999 FTE',
            multiplier=0.6,
        )
        cls.level_base, _c = models.SupportLevel.objects.get_or_create(
            name='Standard',
            multiplier=1.0,
        )
        cls.level_other, _c = models.SupportLevel.objects.get_or_create(
            name='Higher',
            multiplier=2.0,
        )
        cls.currency_base, _c = models.Currency.objects.get_or_create(
            code='GBP',
            region='GBR',
        )
        cls.currency_other, _c = models.Currency.objects.get_or_create(
            code='EUR',
            region='EMU',
        )
        cls.band_base, _c = models.Band.objects.get_or_create(
            size=cls.size_base,
            country='GB',
            currency=cls.currency_base,
            level=cls.level_base,
            fee=1000,
            billing_agent=cls.agent_default,
            base=True,
        )
        cls.band_other_one, _c = models.Band.objects.get_or_create(
            size=cls.size_base,
            country='GB',
            currency=cls.currency_base,
            level=cls.level_base,
            fee=1001,
            billing_agent=cls.agent_default,
        )
        cls.band_other_two, _c = models.Band.objects.get_or_create(
            size=cls.size_other,
            country='BE',
            currency=cls.currency_other,
            level=cls.level_other,
            billing_agent=cls.agent_other,
            fee=2000,
            warnings='Oh no!'
        )
        cls.band_other_three, _c = models.Band.objects.get_or_create(
            size=cls.size_base,
            country='GB',
            currency=cls.currency_base,
            level=cls.level_base,
            fee=1500,
            billing_agent=cls.agent_default,
        )
        cls.band_fixed_fee, _c = models.Band.objects.get_or_create(
            size=cls.size_other,
            country='FR',
            currency=cls.currency_other,
            level=cls.level_other,
            fee=7777,
            fixed_fee=True,
            billing_agent=cls.agent_other,
        )
        cls.supporter_one, _c = models.Supporter.objects.get_or_create(
            name='Birkbeck, University of London',
            ror='https://ror.org/02mb95055',
            band=cls.band_base,
            active=True,
        )
        cls.supporter_one.contacts.add(cls.user_supporter)
        cls.supporter_one.save()
        cls.supporter_two, _c = models.Supporter.objects.get_or_create(
            name='University of Sussex',
            band=cls.band_other_one,
            active=True,
        )
        cls.supporter_two.contacts.add(cls.user_supporter)
        cls.supporter_two.save()
        cls.supporter_three, _c = models.Supporter.objects.get_or_create(
            name='University of Essex',
            band=cls.band_other_three,
            active=True,
        )
        cls.supporter_three.contacts.add(cls.user_supporter)
        cls.supporter_three.save()
        cls.supporter_four, _c = models.Supporter.objects.get_or_create(
            name='University of Antwerp',
            band=cls.band_other_two,
            active=True,
        )
        cls.supporter_four.contacts.add(cls.user_supporter)
        cls.supporter_four.save()
        cls.fake_indicator = 'ABC.DEF.GHI'
        cls.custom_page, created = Page.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(cls.press),
            object_id=cls.press.pk,
            name='become-a-supporter',
            display_name='Become a Supporter',
        )

    @classmethod
    def tearDownClass(cls):
        cls.custom_page.delete()
        cls.supporter_four.delete()
        cls.supporter_three.delete()
        cls.supporter_two.delete()
        cls.supporter_one.delete()
        cls.band_other_two.delete()
        cls.band_other_one.delete()
        cls.band_base.delete()
        cls.currency_other.delete()
        cls.currency_base.delete()
        cls.level_other.delete()
        cls.level_base.delete()
        cls.size_other.delete()
        cls.size_base.delete()
        cls.agent_other.delete()
        cls.agent_default.delete()
        cls.user_agent.save()
        cls.user_staff.save()
        cls.user_supporter.delete()
        cls.press.delete()
        super().tearDownClass()

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
        self.agent_other.default = True
        self.agent_other.save()
        self.agent_default.refresh_from_db()
        self.agent_other.refresh_from_db()

        # Get test values
        other_has_country = bool(self.agent_other.country)
        default_still_default = self.agent_default.default

        # Restore test data
        self.agent_default.default = True
        self.agent_default.save()
        self.agent_other.country = 'GB'
        self.agent_other.save()

        # Run test
        self.assertFalse(other_has_country)
        self.assertFalse(default_still_default)

    def test_currency_exchange_rate(self):
        with patch(
            'plugins.consortial_billing.logic.latest_multiplier_for_indicator'
        ) as latest_multiplier:
            self.currency_other.exchange_rate
            self.assertIn(
                plugin_settings.RATE_INDICATOR,
                latest_multiplier.call_args.args,
            )
            self.assertIn(
                self.currency_other.region,
                latest_multiplier.call_args.args,
            )
            self.assertIn(
                self.currency_other.region,
                latest_multiplier.call_args.args,
            )

    def test_band_economic_disparity(self):
        with patch(
            'plugins.consortial_billing.logic.latest_multiplier_for_indicator'
        ) as latest_multiplier:
            self.band_other_two.economic_disparity
            self.assertIn(
                plugin_settings.DISPARITY_INDICATOR,
                latest_multiplier.call_args.args,
            )
            self.assertIn(
                self.band_other_two.country.alpha3,
                latest_multiplier.call_args.args,
            )
            self.assertIn(
                self.band_base.country.alpha3,
                latest_multiplier.call_args.args,
            )

    def test_band_calculate_fee(self):
        with patch(
            'plugins.consortial_billing.logic.latest_multiplier_for_indicator',
            return_value=(0.85, ''),
        ) as latest_multiplier:
            fee, warnings = self.band_other_two.calculate_fee()
            expected_fee = round(1000 * 0.6 * 2.0 * 0.85 * 0.85, -1)
            latest_multiplier.assert_called()
            self.assertEqual(fee, expected_fee)

    def test_band_determine_billing_agent(self):
        agent = self.band_base.determine_billing_agent()
        self.assertEqual(agent, self.agent_default)
        agent = self.band_other_two.determine_billing_agent()
        self.assertEqual(agent, self.agent_other)

    def test_band_save(self):
        with patch.object(
            self.band_other_two,
            'calculate_fee',
            return_value=(2000, '')
        ) as calculate_fee:
            self.band_other_two.fee = None
            self.band_other_two.save()
            calculate_fee.assert_called_once()
