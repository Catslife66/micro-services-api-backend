# Generated by Django 5.2 on 2025-04-29 10:57

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_rename_subscription_usersubscription_subscription_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscriptionplanprice',
            options={'ordering': ['order', 'featured', '-updated_at']},
        ),
        migrations.AddField(
            model_name='subscriptionplanprice',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 4, 29, 10, 57, 49, 679415, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscriptionplanprice',
            name='featured',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='subscriptionplanprice',
            name='order',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='subscriptionplanprice',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
