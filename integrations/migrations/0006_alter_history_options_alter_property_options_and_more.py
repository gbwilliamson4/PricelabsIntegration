# Generated by Django 4.1.7 on 2023-03-24 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0005_property_info_motopress_rates_request_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='history',
            options={'verbose_name_plural': 'History'},
        ),
        migrations.AlterModelOptions(
            name='property',
            options={'verbose_name_plural': 'Properties'},
        ),
        migrations.AlterModelOptions(
            name='property_info',
            options={'verbose_name_plural': 'Property Info'},
        ),
        migrations.AddField(
            model_name='property_info',
            name='accomodation_id',
            field=models.IntegerField(default=5),
            preserve_default=False,
        ),
    ]
