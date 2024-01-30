from django import forms
from django.utils import timezone

from plugins.consortial_billing import models, logic


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
        """
        Populates a band object matching the form input.
        If there is already a matching object, it is returned
        rather than a new one to prevent duplicate bands from proliferating.
        """
        band = super().save(commit=False)
        try:
            # First check if there's a fixed fee band
            # that should be used for this supporter
            billing_agent = logic.determine_billing_agent(band.country)
            saved_band = models.Band.objects.filter(
                level=band.level,
                size=band.size,
                country=band.country,
                currency=band.currency,
                billing_agent=billing_agent,
                fixed_fee=True,
                base=False,
            ).latest('datetime')
            return saved_band
        except models.Band.DoesNotExist:
            # Otherwise, build the band in all its detail
            # and create it if no identical one already exists
            band.billing_agent = band.determine_billing_agent()
            band.fee, band.warnings = band.calculate_fee()
            if commit:
                band, created = models.Band.objects.get_or_create(
                    level=band.level,
                    size=band.size,
                    country=band.country,
                    currency=band.currency,
                    fee=band.fee,
                    warnings=band.warnings,
                    billing_agent=band.billing_agent,
                    datetime__year=timezone.now().year,
                    display=True,
                    base=False,
                )
            return band


class SupporterForm(forms.ModelForm):

    class Meta:
        model = models.Supporter
        fields = [
            'name',
            'ror',
            'address',
            'postal_code',
            'display',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
