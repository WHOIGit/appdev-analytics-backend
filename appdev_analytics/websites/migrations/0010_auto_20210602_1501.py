# Generated by Django 3.1.10 on 2021-06-02 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websites', '0009_website_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='website',
            name='ga4_property_id',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
