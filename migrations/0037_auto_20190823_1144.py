# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-23 10:44
from __future__ import unicode_literals

import django.core.files.storage
from django.db import migrations, models
import plugins.consortial_billing.models


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0036_banding_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='file',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/Users/ajrbyers/janeway/src/media'), upload_to=plugins.consortial_billing.models.file_upload_path),
        ),
    ]
