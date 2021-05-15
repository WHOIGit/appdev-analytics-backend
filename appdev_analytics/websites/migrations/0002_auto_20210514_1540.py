# Generated by Django 3.1.10 on 2021-05-14 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websites', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='website',
            name='url',
        ),
        migrations.AddField(
            model_name='website',
            name='domain',
            field=models.CharField(default='whoi.edu', max_length=200, unique=True),
            preserve_default=False,
        ),
    ]