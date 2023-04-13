__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch, Mock

from django.test import TestCase
from plugins.consortial_billing import utils, models
from utils.testing import helpers


class (TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_supporter = helpers.create_user('user_supporter@example.org')
        cls.user_staff = helpers.create_user('user_billing_staff@example.org')
        cls.user_agent = helpers.create_user('user_agent@example.org')
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
        cls.band_other, _c = models.Band.objects.get_or_create(
            size=cls.size_other,
            country='BE',
            currency=cls.currency_other,
            level=cls.level_other,
            billing_agent=cls.agent_other,
            fee=2000,
        )
        cls.supporter, _c = models.Supporter.objects.get_or_create(
            name='Birkbeck, University of London',
            ror='https://ror.org/02mb95055',
            band=cls.band_base,
        )
        cls.supporter.contacts.add(cls.user_supporter)
        cls.supporter.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.supporter.delete()
        cls.band_other.delete()
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

    def test_band_calculate_fee(self):
        with patch(
            'plugins.consortial_billing.utils.get_economic_disparity',
            return_value=(0.7, ''),
        ) as disparity:
            with patch(
                'plugins.consortial_billing.utils.get_exchange_rate',
                return_value=(0.85, ''),
            ) as rate:
                fee, warnings = self.band_other.calculate_fee()
                expected_fee = round(1000 * 0.6 * 2.0 * 0.7 * 0.85, -1)
                disparity.assert_called()
                rate.assert_called()
                self.assertEqual(fee, expected_fee)

    def test_band_determine_billing_agent(self):
        agent = self.band_base.determine_billing_agent()
        self.assertEqual(agent, self.agent_default)
        agent = self.band_other.determine_billing_agent()
        self.assertEqual(agent, self.agent_other)

    def test_band_save(self):
        with patch.object(
            self.band_other,
            'calculate_fee',
            return_value=(2000, '')
        ) as calculate_fee:
            self.band_other.fee = None
            self.band_other.save()
            calculate_fee.assert_called_once()
