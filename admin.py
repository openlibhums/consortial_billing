from django.contrib import admin

from plugins.consortial_billing.models import *
from core import models as core_models


class BillingAgentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('users',)


class BandingAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'default_price', 'billing_agent', 'display')
    list_filter = ('currency', 'billing_agent', 'display')
    search_fields = ('name',)


admin_list = [
    (Institution, ),
    (Banding, BandingAdmin),
    (Renewal,),
    (BillingAgent, BillingAgentAdmin),
    (ExcludedUser,),
    (Poll,),
    (Option,),
    (IncreaseOptionBand,),
    (Vote,),
    (SupportLevel,),
]

[admin.site.register(*t) for t in admin_list]
