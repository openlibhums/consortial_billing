import csv
import os
import uuid

from django.contrib import admin
from django.conf import settings

from plugins.consortial_billing import models
from core import files


class BandInline(admin.TabularInline):
    model = models.Band
    extra = 0


class BillingAgentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'country',
        'default',
    )
    list_editable = (
        'name',
        'country',
        'default',
    )
    raw_id_fields = (
        'users',
    )
    inlines = [
        BandInline,
    ]


class SupporterSizeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'is_consortium',
        'description',
        'multiplier',
        'internal_notes',
    )
    list_editable = (
        'name',
        'is_consortium',
        'description',
        'multiplier',
        'internal_notes',
    )
    list_filter = (
        'is_consortium',
    )
    inlines = [
        BandInline,
    ]


class SupportLevelAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'description',
        'multiplier',
        'internal_notes',
    )
    list_editable = (
        'name',
        'description',
        'multiplier',
        'internal_notes',
    )
    inlines = [
        BandInline,
    ]


class CurrencyAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'code',
        'region',
        '_exchange_rate',
        'internal_notes',
    )
    list_editable = (
        'code',
        'region',
        'internal_notes',
    )
    readonly_fields = (
        '_exchange_rate',
    )
    inlines = [
        BandInline,
    ]

    def _exchange_rate(self, obj):
        if obj:
            rate, warnings = obj.exchange_rate
            return rate
        else:
            return ''


class BandAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'size',
        'country',
        'currency',
        'level',
        'fee',
        'datetime',
        'billing_agent',
        'display',
        'base',
    )
    list_filter = (
        'base',
        'datetime',
        'size',
        'currency',
        'level',
        'fee',
        'billing_agent',
        'display',
        'country',
    )
    date_hierarchy = 'datetime'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                'size',
                'country',
                'currency',
                'level',
                'fee',
                'warnings',
                'datetime',
                'billing_agent',
            )
        else:
            return (
                'datetime',
                'warnings',
            )


def export_supporters(modeladmin, request, queryset):
    headers = ['Name', 'Active', 'First Name', 'Last Name', 'Email']
    filename = '{uuid}.csv'.format(uuid=uuid.uuid4())
    filepath = os.path.join(settings.BASE_DIR, 'files', 'temp', filename)
    with open(filepath, 'w') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        for inst in queryset:
            writer.writerow([
                inst.name,
                inst.active,
                inst.first_name,
                inst.last_name,
                inst.email_address,
            ])

    return files.serve_temp_file(filepath, filename)


export_supporters.short_description = "Export Supporters"


class SupporterAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'address',
        'postal_code',
        'country',
        'size',
        'level',
        'fee',
        'currency',
        'billing_agent',
        'active',
        'display',
    )
    search_fields = (
        'name',
        'address',
        'postal_code',
        'contacts__first_name',
        'contacts__last_name',
        'contacts__email',
    )
    list_filter = (
        'active',
        'band__size',
        'band__level',
        'band__currency',
        'band__country',
    )
    raw_id_fields = (
        'contacts',
        'band',
        'old_bands',
    )
    actions = [export_supporters]


admin_list = [
    (models.SupporterSize, SupporterSizeAdmin),
    (models.SupportLevel, SupportLevelAdmin),
    (models.Currency, CurrencyAdmin),
    (models.Supporter, SupporterAdmin),
    (models.Band, BandAdmin),
    (models.BillingAgent, BillingAgentAdmin),
]


[admin.site.register(*t) for t in admin_list]
