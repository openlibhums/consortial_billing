# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-05-10 12:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='billing_agent',
            field=models.ForeignKey(blank=True, null=True, default='', on_delete=django.db.models.deletion.CASCADE, to='consortial_billing.BillingAgent'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='institution',
            name='consortium',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='consortial_billing.Institution'),
        ),
        migrations.AddField(
            model_name='institution',
            name='display',
            field=models.BooleanField(default=True),
        ),
    ]
