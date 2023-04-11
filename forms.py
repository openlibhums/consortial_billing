from django import forms
from django.utils import timezone

from plugins.consortial_billing import models


class BandForm(forms.ModelForm):
    class Meta:
        model = models.Band
        fields = [
            'country',
            'currency',
            'size',
            'level',
            'fee',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].required = True
        self.fields['currency'].required = True
        self.fields['size'].required = True
        self.fields['level'].required = True
        self.fields['fee'].required = False
        self.fields['fee'].disabled = True

    def save(self, commit=True):
        band = super().save(commit=False)
        band.fee, band.warnings = band.calculate_fee()
        band.billing_agent = band.determine_billing_agent()
        if commit:
            band, created = models.Band.objects.get_or_create(
                level=self.cleaned_data['level'],
                size=self.cleaned_data['size'],
                country=self.cleaned_data['country'],
                currency=self.cleaned_data['currency'],
                fee=band.fee,
                warnings=band.warnings,
                billing_agent=band.billing_agent,
                datetime__year=timezone.now().year,
            )
        return band


class SupporterForm(forms.ModelForm):

    class Meta:
        model = models.Supporter
        fields = [
            'name',
            'address',
            'postal_code',
            'display',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
