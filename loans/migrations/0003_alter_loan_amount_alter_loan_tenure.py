# Generated by Django 5.1.6 on 2025-02-28 04:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0002_loan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(1000, message='Minimum loan amount is ₹1,000'), django.core.validators.MaxValueValidator(100000, message='Maximum loan amount is ₹100,000')]),
        ),
        migrations.AlterField(
            model_name='loan',
            name='tenure',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(3, message='Minimum tenure is 3 months'), django.core.validators.MaxValueValidator(24, message='Maximum tenure is 24 months')]),
        ),
    ]
