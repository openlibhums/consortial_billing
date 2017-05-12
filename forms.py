from datetime import timedelta

from django.utils import timezone
from django import forms

from plugins.consortial_billing import models


class Institution(forms.ModelForm):
    class Meta:
        model = models.Institution
        fields = ('first_name', 'last_name', 'email_address', 'name', 'address', 'postal_code', 'country', 'display')


class Renewal(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        institution = kwargs.pop('institution', None)
        super(Renewal, self).__init__(*args, **kwargs)

        if institution:
            self.fields['date'].initial = timezone.now() + timedelta(days=365)
            self.fields['amount'].initial = institution.banding.default_price
            self.fields['currency'].initial = institution.banding.currency

    class Meta:
        model = models.Renewal
        fields = ('date', 'amount', 'currency')