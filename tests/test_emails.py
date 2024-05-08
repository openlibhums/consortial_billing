__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch

from plugins.consortial_billing.tests import test_models
from plugins.consortial_billing.notifications import emails

CBE = 'plugins.consortial_billing.notifications.emails'


class EmailTests(test_models.TestCaseWithData):

    @patch(f'{CBE}.notify_helpers.send_email_with_body_from_setting_template')
    def test_email_agent_about_signup(self, send_email):
        emails.email_agent_about_signup(
            request=self.request,
            supporter=self.supporter_bbk,
        )
        self.assertIn(
            self.supporter_bbk.band.billing_agent.agentcontact_set.first().email,
            send_email.call_args.args[3],
        )
        self.assertIn(
            'new_signup_email',
            send_email.call_args.args,
        )
        self.assertIn(
            'subject_new_signup_email',
            send_email.call_args.args,
        )
        send_email.assert_called()

    @patch(f'{CBE}.notify_helpers.send_email_with_body_from_setting_template')
    def test_email_supporter_to_confirm(self, send_email):
        emails.email_supporter_to_confirm(
            request=self.request,
            supporter=self.supporter_bbk,
        )
        self.assertIn(
            self.supporter_bbk.supportercontact_set.first().email,
            send_email.call_args.args[3],
        )
        self.assertIn(
            'signup_confirmation_email',
            send_email.call_args.args,
        )
        self.assertIn(
            'subject_signup_confirmation_email',
            send_email.call_args.args,
        )
        send_email.assert_called()
