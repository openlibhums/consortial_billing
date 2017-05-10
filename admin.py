from django.contrib import admin

from plugins.consortial_billing.models import *

admin_list = [
    (Institution, ),
    (Banding,),
    (Renewal,),
    (BillingAgent,),
    ]

[admin.site.register(*t) for t in admin_list]
