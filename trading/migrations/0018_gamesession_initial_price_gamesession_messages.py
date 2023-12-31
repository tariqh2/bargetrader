# Generated by Django 4.2.4 on 2023-09-03 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trading", "0017_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamesession",
            name="initial_price",
            field=models.DecimalField(decimal_places=2, default=70, max_digits=10),
        ),
        migrations.AddField(
            model_name="gamesession",
            name="messages",
            field=models.ManyToManyField(to="trading.message"),
        ),
    ]
