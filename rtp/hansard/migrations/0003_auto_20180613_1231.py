# Generated by Django 2.0.5 on 2018-06-13 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hansard', '0002_auto_20180612_1244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sentence',
            name='time_talk_started',
            field=models.TimeField(null=True),
        ),
    ]
