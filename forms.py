from django import forms
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured

from core import forms as core_forms
from core.models import Account
from plugins.consortial_billing import models as supporter_models, logic


class BaseBandForm(forms.ModelForm):

    __original_category = None

    class Meta:
        model = supporter_models.Band
        fields = [
            'country',
            'currency',
            'size',
            'level',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].required = True
        self.fields['currency'].required = True
        self.fields['size'].required = True
        self.fields['level'].required = True
        if self.instance:
            self.__original_category = self.instance.category

    def save(self, commit=True):
        """
        Populates a band object matching the form input.
        If there is already a matching object, it is returned
        rather than a new one to prevent duplicate bands from proliferating.
        """

        # Get an unsaved band for matching purposes
        unsaved_band = super().save(commit=False)
        unsaved_band.billing_agent = logic.determine_billing_agent(unsaved_band.country)

        if unsaved_band.category == 'special':
            # The user wants to control the fee manually for this one supporter.
            # In this case, the form should behave as normal.
            band = unsaved_band
            if self.instance and self.__original_category == 'calculated':
                # The user has changed an existing band from calculated to special.
                # In this case we want to create a new band object so we do not throw off
                # other supporter fees that may be dependant on the existing band.
                band.pk = None
        elif unsaved_band.category == 'calculated':
            # For calculated bands, we try to avoid duplicates to make management easier
            unsaved_band.fee, unsaved_band.warnings = unsaved_band.calculate_fee()
            kwargs = {
                'level': unsaved_band.level,
                'size': unsaved_band.size,
                'country': unsaved_band.country,
                'currency': unsaved_band.currency,
                'billing_agent': unsaved_band.billing_agent,
                'category': unsaved_band.category,
            }

            try:
                # If there's an appropriate calculated band, use it.
                kwargs['fee'] = unsaved_band.fee
                kwargs['warnings'] = unsaved_band.warnings
                kwargs['datetime__year'] = timezone.now().year
                band = supporter_models.Band.objects.filter(**kwargs).latest()
            except supporter_models.Band.DoesNotExist:
                # Otherwise, use the unsaved band.
                band = unsaved_band

        if commit:
            band.save()
        return band


class SignupBandForm(BaseBandForm):

    class Meta(BaseBandForm.Meta):
        fields = [
            'country',
            'currency',
            'size',
            'level',
            'fee',
            'category',
        ]
        widgets = {
            'category': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fee'].required = False
        self.fields['fee'].disabled = True


class EditBandForm(BaseBandForm):

    class Meta(BaseBandForm.Meta):
        fields = [
            'level',
            'size',
            'country',
            'currency',
            'fee',
            'category',
            'billing_agent',
            'warnings',
        ]
        help_texts = {
            'billing_agent': 'To change the billing agent, select the appropriate country and currency.',
            'fee': 'To edit this field, set the band category to special. To auto-calculate it, set the band category to calculated.',
            'category': 'Whether the fee is calculated or special for this supporter',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['billing_agent'].disabled = True
        self.fields['warnings'].disabled = True
        self.fields['fee'].required = True
        all_category_choices = supporter_models.BAND_CATEGORY_CHOICES
        choices_without_base = [c for c in all_category_choices if c[0] != 'base']
        self.fields['category'].widget.choices = choices_without_base
        if self.instance:
            if self.instance.category == 'special':
                self.fields['fee'].disabled = False
            elif self.instance.category == 'calculated':
                self.fields['fee'].disabled = True
                self.fields['fee'].required = False


class SupporterSignupForm(forms.ModelForm):

    class Meta:
        model = supporter_models.Supporter
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

    def save(self, commit=True, band=None):
        supporter = super().save(commit=False)
        if band:
            if supporter.band and supporter.band != band:
                supporter_models.OldBand.objects.get_or_create(
                    supporter=supporter,
                    band=supporter.band,
                )
            supporter.band = band
            supporter.prospective_band = None
            supporter.country = band.country
        if commit:
            supporter.save()
        return supporter


class EditSupporterForm(SupporterSignupForm):

    class Meta(SupporterSignupForm.Meta):
        fields = [
            'name',
            'ror',
            'address',
            'postal_code',
            'display',
            'active',
            'internal_notes',
        ]


class AccountAdminSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'type': 'search'}
        ),
        label='Search existing accounts to add a new contact',
    )
