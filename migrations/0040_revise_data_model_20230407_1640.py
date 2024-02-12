# Generated by Django 3.2.18 on 2023-04-08 15:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields
import plugins.consortial_billing.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("consortial_billing", "0039_auto_20221216_1329"),
    ]

    operations = [


        # CREATE NEW MODEL -- CURRENCY
        migrations.CreateModel(
            name="Currency",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Three-letter currency code, e.g. EUR",
                        max_length=3
                    ),
                ),
                (
                    "region",
                    models.CharField(
                        choices=[
                            ("EMU", "Euro area"),
                            ("GBR", "United Kingdom"),
                            ("USA", "United States"),
                        ],
                        help_text="The region or country associated with "
                                  "this currency in World Bank data",
                        max_length=3,
                    ),
                ),
                (
                    "internal_notes",
                    models.CharField(
                        blank=True,
                        help_text="Internal notes on how this was configured, "
                                  "for when it needs updating next",
                        max_length=255,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Currencies",
                "ordering": ("code",),
            },
        ),


        # CREATE NEW MODEL -- INSTITUTION SIZE
        migrations.CreateModel(
            name="SupporterSize",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="The name of the size band, "
                                  "e.g. Large Institution",
                        max_length=20
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        help_text="How size is determined, e.g. 0-4999 FTE "
                                  "staff for an institution",
                        max_length=200,
                    ),
                ),
                (
                    "multiplier",
                    models.FloatField(
                        default=1,
                        help_text="The base rate is multiplied by this as "
                                  "part of the support fee calculation",
                    ),
                ),
                (
                    "internal_notes",
                    models.CharField(
                        blank=True,
                        help_text="Internal notes on how this was configured, "
                                  "for when it needs updating next",
                        max_length=255,
                    ),
                ),
                (
                    "is_consortium",
                    models.BooleanField(
                        default=False, help_text="Whether this is a consortium"
                    ),
                ),
            ],
            options={
                "ordering": ("is_consortium", "name"),
            },
        ),


        # ADD AND ALTER FIELDS -- SUPPORT LEVEL
        migrations.AddField(
            model_name="supportlevel",
            name="internal_notes",
            field=models.CharField(
                blank=True,
                help_text="Internal notes on how this was configured, "
                          "for when it needs updating next",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="supportlevel",
            name="multiplier",
            field=models.FloatField(
                default=1,
                help_text="The base rate is multiplied by this as part "
                          "of the support fee calculation",
            ),
        ),
        migrations.AlterField(
            model_name="supportlevel",
            name="description",
            field=models.CharField(
                blank=True,
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="supportlevel",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="The level of support, e.g. Standard or Gold",
                max_length=30,
                null=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="supportlevel",
            options={"ordering": ("-multiplier", "name")},
        ),


        # ADD AND ALTER FIELDS -- BILLING AGENT
        migrations.AddField(
            model_name="billingagent",
            name="country",
            field=django_countries.fields.CountryField(
                blank=True,
                help_text="If selected, will route all signups "
                          "in this country to this agent.",
                max_length=2,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="billingagent",
            name="default",
            field=models.BooleanField(
                default=False,
                help_text="Designates this as the default billing agent. ",
            ),
        ),
        migrations.AddField(
            model_name='billingagent',
            name='redirect_url',
            field=models.URLField(
                blank=True,
                help_text="If populated, the user will be redirected here "
                          "to complete the sign-up process",
                null=True,
            ),
        ),


        # ADD AND ALTER FIELDS -- BANDING
        migrations.AddField(
            model_name="banding",
            name="base",
            field=models.BooleanField(
                default=False,
                help_text="Select if this is the base band to represent "
                          "the base fee, country, and currency for a "
                          "given support level.",
            ),
        ),
        migrations.AddField(
            model_name="banding",
            name="country",
            field=django_countries.fields.CountryField(
                blank=True,
                max_length=2,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="banding",
            name="datetime",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
            ),
        ),
        migrations.AddField(
            model_name="banding",
            name="fee",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name='Annual fee',
            ),
        ),
        migrations.AddField(
            model_name="banding",
            name="level",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="consortial_billing.supportlevel",
                verbose_name="Support level",
            ),
        ),
        migrations.AddField(
            model_name="banding",
            name="currency_temp",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="consortial_billing.currency",
                verbose_name="Preferred currency",
            ),
        ),
        migrations.AddField(
            model_name="banding",
            name="size_temp",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="consortial_billing.supportersize",
                verbose_name="Institution size",
            ),
        ),
        migrations.AddField(
            model_name='banding',
            name='warnings',
            field=models.CharField(
                blank=True,
                help_text='Warning messages from the fee calculator',
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="banding",
            name="billing_agent",
            field=models.ForeignKey(
                blank=True,
                help_text="Who is responsible for billing this supporter",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="consortial_billing.billingagent",
            ),
        ),
        migrations.AlterField(
            model_name="banding",
            name="name",
            field=models.CharField(
                blank=True,
                null=True,
                unique=False,
                max_length=200,
            ),
        ),


        # ADD AND ALTER FIELDS -- INSTITUTION
        migrations.AddField(
            model_name="institution",
            name="band_temp",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="consortial_billing.Banding",
                help_text='Current band',
            ),
        ),
        migrations.AddField(
            model_name="institution",
            name="old_bands",
            field=models.ManyToManyField(
                blank=True,
                null=True,
                help_text='Old bands for this supporter',
                related_name='supporter_history',
                to='consortial_billing.Banding',
            ),
        ),
        migrations.AddField(
            model_name="institution",
            name="contacts",
            field=models.ManyToManyField(
                blank=True,
                help_text="Who can be contacted at this supporter",
                null=True,
                related_name="contact_for_supporter",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="institution",
            name="country_temp",
            field=django_countries.fields.CountryField(
                blank=True,
                max_length=2,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='institution',
            name='ror',
            field=models.URLField(
                blank=True,
                validators=[plugins.consortial_billing.models.validate_ror],
                help_text='Research Organization Registry identifier (URL)',
                verbose_name='ROR',
            ),
        ),
        migrations.AlterField(
            model_name="institution",
            name="active",
            field=models.BooleanField(
                default=False,
                help_text="Whether the supporter is active",
            ),
        ),
        migrations.AlterField(
            model_name="institution",
            name="address",
            field=models.TextField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Billing address",
            ),
        ),
        migrations.AlterField(
            model_name="institution",
            name="display",
            field=models.BooleanField(
                default=True,
                help_text="May we include your institution name "
                          "in our public list of supporters?",
            ),
        ),
        migrations.AlterField(
            model_name="institution",
            name="name",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="Institution name",
            ),
        ),
        migrations.AlterField(
            model_name="institution",
            name="postal_code",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="institution",
            options={"ordering": ("name",)},
        ),


    ]
