# Generated by Django 3.1.10 on 2021-05-25 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websites', '0006_website_log_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='website',
            name='log_type',
            field=models.CharField(choices=[('1', 'Apache'), ('2', 'NGINX')], default='1', max_length=32),
        ),
    ]
