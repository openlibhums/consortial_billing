from rest_framework import serializers

from plugins.consortial_billing import models


class BillingAgent(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.BillingAgent
        fields = ('name',)


class BandingSerializer(serializers.HyperlinkedModelSerializer):

    billing_agent = BillingAgent()

    class Meta:
        model = models.Banding
        fields = ('name', 'currency', 'default_price', 'billing_agent')


class InstitutionSerializer(serializers.HyperlinkedModelSerializer):

    banding = BandingSerializer()

    class Meta:
        model = models.Institution
        fields = ('pk', 'name', 'first_name', 'last_name', 'email_address', 'active', 'display', 'banding')
