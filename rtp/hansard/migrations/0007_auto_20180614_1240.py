# Generated by Django 2.0.5 on 2018-06-14 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hansard', '0006_auto_20180614_0355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='debatereference',
            name='subdebate1_title',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='debatereference',
            name='subdebate2_title',
            field=models.CharField(max_length=1024, null=True),
        ),
    ]