from django import forms
from plugins.consortial_billing import models


class Institution(forms.ModelForm):
    class Meta:
        model = models.Institution
        fields = ('first_name', 'last_name', 'email_address', 'name', 'address', 'postal_code', 'country', 'display')