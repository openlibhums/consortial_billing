# Generated by Django 3.2.18 on 2023-10-11 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0044_auto_20230427_1057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='supportlevel',
            options={'ordering': ('order', 'name')},
        ),
        migrations.RemoveField(
            model_name='supportlevel',
            name='multiplier',
        ),
        migrations.AddField(
            model_name='supportlevel',
            name='order',
            field=models.IntegerField(
                blank=True,
                help_text='The order in which to display the levels '
                          'from highest to lowest.',
                null=True
            ),
        ),
    ]
