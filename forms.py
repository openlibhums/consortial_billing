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

        # Get an unsaved band for matching purposes
        unsaved_band = super().save(commit=False)
        unsaved_band.billing_agent = logic.determine_billing_agent(unsaved_band.country)
        unsaved_band.fee, unsaved_band.warnings = unsaved_band.calculate_fee()
        kwargs = {
            'level': unsaved_band.level,
            'size': unsaved_band.size,
            'country': unsaved_band.country,
            'currency': unsaved_band.currency,
            'billing_agent': unsaved_band.billing_agent,
            'display': True,
            'base': False,
        }

        try:
            # If there's an appropriate fixed-fee band, use it.
            kwargs['fixed_fee'] = True
            band = models.Band.objects.filter(**kwargs).latest()

        except models.Band.DoesNotExist:
            try:
                # Otherwise, if there's an appropriate dynamic-fee band, use it.
                kwargs['fixed_fee'] = False
                kwargs['fee'] = unsaved_band.fee
                kwargs['warnings'] = unsaved_band.warnings
                kwargs['datetime__year'] = timezone.now().year
                band = models.Band.objects.filter(**kwargs).latest()
            except models.Band.DoesNotExist:
                # Otherwise, use the unsaved band.
                band = unsaved_band

        finally:
            if commit:
                band.save()
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
