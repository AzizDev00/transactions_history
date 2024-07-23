# Generated by Django 5.0.6 on 2024-07-22 12:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0002_alter_incometype_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='income',
            name='manual_income_image',
            field=models.ImageField(blank=True, null=True, upload_to='manual_income_types/'),
        ),
        migrations.AlterField(
            model_name='income',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='incomes/'),
        ),
        migrations.AlterField(
            model_name='income',
            name='income_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='history.incometype'),
        ),
        migrations.AlterField(
            model_name='income',
            name='manual_income_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incometype',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]