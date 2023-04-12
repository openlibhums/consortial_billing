# Generated by Django 3.2.18 on 2023-04-09 08:17

from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('consortial_billing', '0041_migrate_data_20230409_0913'),
    ]

    operations = [


        # REMOVE UNNEEDED FIELDS
        migrations.RemoveField(
            model_name="banding",
            name="name",
        ),
        migrations.RemoveField(
            model_name="banding",
            name="redirect_url",
        ),
        migrations.RemoveField(
            model_name="supportlevel",
            name="order",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="billing_agent",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="consortial_billing",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="consortium",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="country",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="email_address",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="last_name",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="multiplier",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="referral_code",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="sort_country",
        ),
        migrations.RemoveField(
            model_name="institution",
            name="supporter_level",
        ),
        migrations.RemoveField(
            model_name="excludeduser",
            name="user",
        ),
        migrations.RemoveField(
            model_name="increaseoptionband",
            name="banding",
        ),
        migrations.RemoveField(
            model_name="increaseoptionband",
            name="option",
        ),
        migrations.RemoveField(
            model_name="poll",
            name="options",
        ),
        migrations.RemoveField(
            model_name="poll",
            name="staffer",
        ),
        migrations.RemoveField(
            model_name="referral",
            name="new_institution",
        ),
        migrations.RemoveField(
            model_name="referral",
            name="referring_institution",
        ),
        migrations.RemoveField(
            model_name="renewal",
            name="institution",
        ),
        migrations.RemoveField(
            model_name="vote",
            name="aye",
        ),
        migrations.RemoveField(
            model_name="vote",
            name="institution",
        ),
        migrations.RemoveField(
            model_name="vote",
            name="no",
        ),
        migrations.RemoveField(
            model_name="vote",
            name="poll",
        ),
        migrations.RemoveField(
            model_name="banding",
            name="default_price",
        ),
        migrations.RemoveField(
            # see also RenameField below
            model_name='banding',
            name='currency',
        ),
        migrations.RemoveField(
            # see also RenameField below
            model_name='banding',
            name='size',
        ),
        migrations.RemoveField(
            # see also RenameField below
            model_name="institution",
            name="banding",
        ),


        # RENAME MIGRATED FIELDS
        migrations.RenameField(
            model_name='banding',
            old_name='currency_temp',
            new_name='currency',
        ),
        migrations.RenameField(
            model_name='banding',
            old_name='size_temp',
            new_name='size',
        ),
        migrations.RenameField(
            model_name='institution',
            old_name='band_temp',
            new_name='band',
        ),


        # RENAME MODELS
        migrations.RenameModel(
            'Institution',
            'Supporter',
        ),
        migrations.RenameModel(
            'Banding',
            'Band',
        ),


        # REMOVE UNNEEDED MODELS
        migrations.DeleteModel(
            name="Signup",
        ),
        migrations.DeleteModel(
            name="ExcludedUser",
        ),
        migrations.DeleteModel(
            name="IncreaseOptionBand",
        ),
        migrations.DeleteModel(
            name="Option",
        ),
        migrations.DeleteModel(
            name="Poll",
        ),
        migrations.DeleteModel(
            name="Referral",
        ),
        migrations.DeleteModel(
            name="Renewal",
        ),
        migrations.DeleteModel(
            name="Vote",
        ),


    ]
