# Generated by Django 3.2.7 on 2021-09-30 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itelapp', '0003_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='best_seller',
            field=models.BooleanField(default=None),
        ),
    ]
