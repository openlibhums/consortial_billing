# Generated by Django 3.2.18 on 2023-04-11 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0042_clean_up_data_model_20230409_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='band',
            name='warnings',
            field=models.CharField(blank=True, help_text='Warning messages from the fee calculator', max_length=255),
        ),
    ]