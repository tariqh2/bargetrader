# Generated by Django 4.2.4 on 2023-09-05 14:51

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trading", "0018_gamesession_initial_price_gamesession_messages"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiplayer",
            name="current_ev",
            field=models.DecimalField(
                decimal_places=4, default=Decimal("0.00"), max_digits=10
            ),
        ),
    ]
