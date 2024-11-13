# Generated by Django 4.2.16 on 2024-11-13 16:21

import core.model_utils
from django.db import migrations
from django.template.defaultfilters import linebreaksbr


def linebreaks_to_brs_in_internal_notes(apps, schema_editor):
    Supporter = apps.get_model('consortial_billing', 'Supporter')
    for supporter in Supporter.objects.all():
        new_notes = linebreaksbr(supporter.internal_notes)
        supporter.internal_notes = new_notes
        supporter.save()


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0056_remove_supporter_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supporter',
            name='internal_notes',
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text='Internal notes on this supporter',
                max_length=500
            ),
        ),
        migrations.RunPython(
            linebreaks_to_brs_in_internal_notes,
            reverse_code=migrations.RunPython.noop,
        )
    ]