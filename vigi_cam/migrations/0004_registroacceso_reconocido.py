# Generated by Django 5.1.5 on 2025-02-03 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vigi_cam', '0003_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='registroacceso',
            name='reconocido',
            field=models.BooleanField(default=False),
        ),
    ]
