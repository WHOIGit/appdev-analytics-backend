# Generated by Django 3.1.10 on 2021-06-02 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websites', '0008_auto_20210525_1327'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
