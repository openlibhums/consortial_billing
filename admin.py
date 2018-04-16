import csv
import os
import uuid

from django.contrib import admin
from django.conf import settings

from plugins.consortial_billing.models import *
from core import files


class BillingAgentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('users',)


class BandingAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'default_price', 'billing_agent', 'display', 'size')
    list_filter = ('currency', 'billing_agent', 'display', 'size')
    search_fields = ('name',)


class ReferralAdmin(admin.ModelAdmin):
    list_display = ('pk', 'referring_institution', 'new_institution', 'datetime')
    list_filter = ('referring_institution',)


def export_institutions(modeladmin, request, queryset):
    headers = ['Name', 'Country', 'Active', 'First Name', 'Last Name', 'Email']
    filename = '{uuid}.csv'.format(uuid=uuid.uuid4())
    filepath = os.path.join(settings.BASE_DIR, 'files', 'temp', filename)
    with open(filepath, 'w') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for inst in queryset:
            writer.writerow([inst.name, inst.country, inst.active, inst.first_name, inst.last_name, inst.email_address])

    return files.serve_temp_file(filepath, filename)


export_institutions.short_description = "Export Institutions"


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'active', 'banding', 'first_name', 'last_name', 'email_address')
    search_fields = ('name', 'first_name', 'last_name', 'email_addres')
    list_filter = ('country', 'banding')
    actions = [export_institutions]


admin_list = [
    (Institution, InstitutionAdmin),
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
