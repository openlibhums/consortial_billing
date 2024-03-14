import csv

from django.contrib import admin
from django.contrib import messages
from django.utils import timezone

from plugins.consortial_billing import models
from core import files


class AgentContactInline(admin.TabularInline):
    model = models.AgentContact
    extra = 0
    raw_id_fields = ('account', 'agent')


class SupporterContactInline(admin.TabularInline):
    model = models.SupporterContact
    extra = 0
    raw_id_fields = ('account', 'supporter')


class SupporterInline(admin.TabularInline):
    model = models.Supporter
    fields = ('name', 'country')
    readonly_fields = ('name', 'country')
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class OldBandInline(admin.TabularInline):
    model = models.OldBand
    raw_id_fields = ('band', 'supporter')
    readonly_fields = ('band', 'supporter')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class BillingAgentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        '_contacts',
        'country',
        'default',
    )
    list_editable = (
        'country',
        'default',
    )
    inlines = [
        AgentContactInline,
    ]

    def _contacts(self, obj):
        if obj and obj.agentcontact_set.exists():
            contacts = obj.agentcontact_set.all()
            return ', '.join([str(contact) for contact in contacts])
        else:
            return ''


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
        'default',
    )
    list_editable = (
        'name',
        'description',
        'order',
        'internal_notes',
        'default',
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
    inlines = [
        SupporterInline,
        OldBandInline,
    ]

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

    # For performance
    list_per_page = 25

    list_display = (
        'name',
        '_contacts',
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
        'supportercontact__account__first_name',
        'supportercontact__account__last_name',
        'supportercontact__account__email',
        'internal_notes',
    )
    list_filter = (
        'active',
        'band__size',
        'band__level',
        'band__currency',
        'band__country',
    )
    raw_id_fields = (
        'band',
    )

    inlines = [
        SupporterContactInline,
        OldBandInline,
    ]

    actions = [
        'export_supporters',
    ]

    def _contacts(self, obj):
        if obj and obj.supportercontact_set.exists():
            contacts = obj.supportercontact_set.all()
            return ', '.join([str(contact) for contact in contacts])
        else:
            return ''

    @admin.action(description="Export selected supporters")
    def export_supporters(self, request, queryset):
        """
        Basic way of exporting supporters.
        It is better to use django's dumpdata if you have access to the command
        line.
        """
        fieldnames = [
            'name',
            'ror',
            'address',
            'postal_code',
            'country',
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
    (models.BillingAgent, BillingAgentAdmin),
    (models.SupporterSize, SupporterSizeAdmin),
    (models.SupportLevel, SupportLevelAdmin),
    (models.Currency, CurrencyAdmin),
    (models.Band, BandAdmin),
    (models.Supporter, SupporterAdmin),
]


[admin.site.register(*t) for t in admin_list]
