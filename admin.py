import csv

from django.contrib import admin
from django.contrib import messages
from django.utils import timezone

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


class SupporterSizeAdmin(admin.ModelAdmin):
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


class SupportLevelAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'description',
        'order',
        'internal_notes',
    )
    list_editable = (
        'name',
        'description',
        'order',
        'internal_notes',
    )


class CurrencyAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'code',
        'symbol',
        'region',
        '_exchange_rate',
        'internal_notes',
    )
    list_editable = (
        'code',
        'symbol',
        'region',
        'internal_notes',
    )
    readonly_fields = (
        '_exchange_rate',
    )

    def _exchange_rate(self, obj):
        if obj:
            rate, warnings = obj.exchange_rate()
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
        'display',
        'fixed_fee',
        'datetime',
        'size',
        'currency',
        'level',
        'fee',
        'billing_agent',
        'country',
    )
    date_hierarchy = 'datetime'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.fixed_fee:
            return (
                'size',
                'country',
                'currency',
                'level',
                'warnings',
                'datetime',
                'base',
            )
        elif obj:
            return (
                'size',
                'country',
                'currency',
                'level',
                'fee',
                'fixed_fee',
                'warnings',
                'datetime',
                'billing_agent',
                'base',
            )
        else:
            return (
                'warnings',
                'datetime',
            )


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
    list_editable = (
        'active',
        'display',
    )
    raw_id_fields = (
        'contacts',
        'band',
        'old_bands',
    )

    actions = [
        'export_supporters',
        'test_action',
    ]

    @admin.action(description="Export selected supporters")
    def export_supporters(self, request, queryset):
        fieldnames = [
            'name',
            'ror',
            'address',
            'postal_code',
            'country',
            'email',
            'first_name',
            'last_name',
            'display',
            'active',
            'size',
            'currency',
            'level',
            'fee',
            'warnings',
            'datetime',
            'billing_agent',
        ]

        timestamp = timezone.now().strftime('%Y-%m-%dT%H-%M-%S')
        filename = f'supporters_export_{timestamp}.csv'
        filepath = files.create_temp_file('', filename)
        with open(filepath, 'w') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for supporter in queryset:
                row = {}
                for fieldname in fieldnames:
                    row[fieldname] = getattr(supporter, fieldname)

                writer.writerow(row)

        count = queryset.count()
        self.message_user(
            request,
            f"Downloaded {count} records",
            messages.SUCCESS,
        )
        return files.serve_temp_file(filepath, filename)


admin_list = [
    (models.SupporterSize, SupporterSizeAdmin),
    (models.SupportLevel, SupportLevelAdmin),
    (models.Currency, CurrencyAdmin),
    (models.Supporter, SupporterAdmin),
    (models.Band, BandAdmin),
    (models.BillingAgent, BillingAgentAdmin),
]


[admin.site.register(*t) for t in admin_list]
