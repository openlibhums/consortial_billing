from datetime import timedelta

from django.utils import timezone
from django import forms

from plugins.consortial_billing import models


class Institution(forms.ModelForm):

    class Meta:
        model = models.Institution
        fields = ('first_name', 'last_name', 'email_address', 'name', 'address', 'postal_code', 'country', 'display')


class InstitutionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(InstitutionForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['address'].required = False
        self.fields['postal_code'].required = False
        self.fields['email_address'].required = False

    class Meta:
        model = models.Institution
        exclude = ('',)

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


class Poll(forms.ModelForm):
    class Meta:
        model = models.Poll
        exclude = ('staffer', 'date_started', 'options', 'processed')


class Option(forms.ModelForm):
    class Meta:
        model = models.Option
        exclude = ('',)


class Banding(forms.Form):

    def __init__(self, *args, **kwargs):
        option = kwargs.pop('option', None)
        super(Banding, self).__init__(*args, **kwargs)

        for banding in models.Banding.objects.all():
            self.fields[str(banding.pk)] = forms.CharField(widget=forms.TextInput(), required=False)
            self.fields[str(banding.pk)].label = banding.name
            self.fields[str(banding.pk)].help_text = banding.currency

            if option:
                try:
                    option_banding = models.IncreaseOptionBand.objects.get(banding=banding, option=option)
                    self.fields[str(banding.pk)].initial = option_banding.price_increase
                except models.IncreaseOptionBand.DoesNotExist:
                    self.fields[str(banding.pk)].initial = ''

    def save(self, *args, **kwargs):
        option = kwargs.pop('option', None)
        for banding in models.Banding.objects.all():
            banding_price = self.cleaned_data.get(str(banding.pk))
            o, c = models.IncreaseOptionBand.objects.get_or_create(option=option,
                                                                   banding=banding,
                                                                   defaults={'price_increase': banding_price})
            if not c:
                o.price_increase = banding_price
                o.save()
