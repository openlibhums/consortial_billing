# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-02 08:45
from __future__ import unicode_literals

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import plugins.consortial_billing.models


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0029_auto_20170726_1046'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('order', models.PositiveIntegerField(default=99)),
            ],
        ),
        migrations.AlterField(
            model_name='poll',
            name='file',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/home/ajrbyers/Code/janeway/src/media'), upload_to=plugins.consortial_billing.models.file_upload_path),
        ),
        migrations.AddField(
            model_name='institution',
            name='supporter_level',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='consortial_billing.SupportLevel'),
        ),
    ]