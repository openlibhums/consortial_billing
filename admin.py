from django.contrib import admin

from plugins.consortial_billing.models import *


class BillingAgentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('users',)


class BandingAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'default_price', 'billing_agent', 'display')
    list_filter = ('currency', 'billing_agent', 'display')
    search_fields = ('name',)


class ReferralAdmin(admin.ModelAdmin):
    list_display = ('pk', 'referring_institution', 'new_institution', 'datetime')
    list_filter = ('referring_institution',)


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
    (Referral, ReferralAdmin),
]


[admin.site.register(*t) for t in admin_list]
