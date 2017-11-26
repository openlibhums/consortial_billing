from mock import Mock

from django.test import TestCase
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied

from security.test_security import TestSecurity
from core import models as core_models
from journal import models as journal_models
from plugins.consortial_billing import models, security


class TestPluginSecurity(TestCase):

    def test_billing_agent_required_with_agent(self):
        func = Mock()
        decorated_func = security.billing_agent_required(func)

        request = self.prepare_request_with_user(self.agent_user_one, self.journal_one)

        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "billing agent required wrongly blocks an agent")

    def test_billing_agent_required_with_regular_user(self):
        func = Mock()
        decorated_func = security.billing_agent_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that reviewer_user_required raises a PermissionDenied exception
            decorated_func(request)

        self.assertFalse(func.called,
                         "billing agent required wrongly allows a non agent to access pages")

    def test_billing_agent_for_institution_required_with_correct_agent(self):
        func = Mock()
        decorated_func = security.billing_agent_for_institution_required(func)

        request = self.prepare_request_with_user(self.agent_user_one, self.journal_one)

        kwargs = {'institution_id': self.institution_one.pk}
        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called, "billing_agent_for_institution_required wrongly blocks an agent")

        kwargs = {'renewal_id': self.renewal_one.pk}
        decorated_func(request, **kwargs)

        self.assertTrue(func.called, "billing_agent_for_institution_required wrongly blocks an agent")

    def test_billing_agent_for_institution_required_with_bad_agent(self):
        func = Mock()
        decorated_func = security.billing_agent_for_institution_required(func)

        request = self.prepare_request_with_user(self.agent_user_two, self.journal_one)

        kwargs = {'institution_id': self.institution_one.pk}
        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_billing_agent_for_institution_required_with_regular_user(self):
        func = Mock()
        decorated_func = security.billing_agent_for_institution_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_one)

        kwargs = {'institution_id': self.institution_one.pk}
        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_agent_for_billing_agent_required_with_agent(self):
        func = Mock()
        decorated_func = security.agent_for_billing_agent_required(func)

        request = self.prepare_request_with_user(self.agent_user_one, self.journal_one)

        kwargs = {'billing_agent_id': self.billing_agent_one.pk}
        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called, "billing agent required wrongly blocks an agent")

    def test_agent_for_billing_agent_required_with_regular_user(self):
        func = Mock()
        decorated_func = security.agent_for_billing_agent_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_one)

        kwargs = {'billing_agent_id': self.billing_agent_one.pk}
        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    @staticmethod
    def create_user(username, roles=None, journal=None):
        """
        Creates a user with the specified permissions.
        :return: a user with the specified permissions
        """
        # check this way to avoid mutable default argument
        if roles is None:
            roles = []

        kwargs = {'username': username}
        user = core_models.Account.objects.create_user(email=username, **kwargs)

        for role in roles:
            resolved_role = core_models.Role.objects.get(name=role)
            core_models.AccountRole(user=user, role=resolved_role, journal=journal).save()

        user.save()

        return user

    @staticmethod
    def create_roles(roles=None):
        """
        Creates the necessary roles for testing.
        :return: None
        """
        # check this way to avoid mutable default argument
        if roles is None:
            roles = []

        for role in roles:
            core_models.Role(name=role, slug=role).save()

    @staticmethod
    def create_journals():
        """
        Creates a set of dummy journals for testing
        :return: a 2-tuple of two journals
        """
        journal_one = journal_models.Journal(code="TST", domain="journal1.localhost")
        journal_one.save()

        journal_two = journal_models.Journal(code="TSA", domain="journal2.localhost")
        journal_two.save()

        return journal_one, journal_two

    def setUp(self):
        self.journal_one, self.journal_two = self.create_journals()
        self.create_roles(["editor", "author", "reviewer", "proofreader", "production", "copyeditor", "typesetter",
                           "proofing_manager", "section-editor"])

        self.agent_user_one = self.create_user("agent_user_one@martineve.com")
        self.agent_user_one.is_active = True
        self.agent_user_one.save()

        self.agent_user_two = self.create_user("agent_user_two@martineve.com")
        self.agent_user_two.is_active = True
        self.agent_user_two.save()

        self.second_user = self.create_user("seconduser@martineve.com", ["reviewer"], journal=self.journal_one)
        self.second_user.is_active = True
        self.second_user.save()

        self.admin_user = self.create_user("adminuser@martineve.com")
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        self.billing_agent_one = models.BillingAgent.objects.create(name='Agent One')
        self.billing_agent_one.users.add(self.agent_user_one)

        self.billing_agent_two = models.BillingAgent.objects.create(name='Agent Two')
        self.billing_agent_two.users.add(self.agent_user_two)

        self.banding_one = models.Banding.objects.create(name='Banding One',
                                                         currency='GBP',
                                                         default_price='100',
                                                         billing_agent=self.billing_agent_one)

        self.banding_two = models.Banding.objects.create(name='Banding Two',
                                                         currency='EUR',
                                                         default_price='150',
                                                         billing_agent=self.billing_agent_two)

        self.institution_one = models.Institution.objects.create(name='Inst One',
                                                                 country='GB',
                                                                 active=True,
                                                                 display=True,
                                                                 banding=self.banding_one,
                                                                 billing_agent=self.billing_agent_one)

        self.institution_two = models.Institution.objects.create(name='Inst Two',
                                                                 country='FR',
                                                                 active=True,
                                                                 display=True,
                                                                 banding=self.banding_two,
                                                                 billing_agent=self.billing_agent_two)

        self.renewal_one = models.Renewal.objects.create(amount=100,
                                                         currency='GBP',
                                                         institution=self.institution_one)

    @staticmethod
    def mock_messages_add(level, message, extra_tags):
        pass

    @staticmethod
    def get_method(field):
        return None

    @staticmethod
    def prepare_request_with_user(user, journal):
        """
        Build a basic request dummy object with the journal set to journal and the user having editor permissions.
        :param user: the user to use
        :param journal: the journal to use
        :return: an object with user and journal properties
        """
        request = Mock(HttpRequest)
        request.user = user
        request.GET = Mock()
        request.GET.get = TestSecurity.get_method
        request.journal = journal
        request._messages = Mock()
        request._messages.add = TestSecurity.mock_messages_add

        return request
