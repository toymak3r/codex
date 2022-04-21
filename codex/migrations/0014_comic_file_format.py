"""Generated by Django 4.0.4 on 2022-04-21 00:44."""

from django.db import migrations, models

import codex.models


class Migration(migrations.Migration):
    """Comic.file_format field."""

    dependencies = [
        ("codex", "0013_int_issue_count_longer_charfields"),
    ]

    operations = [
        migrations.AddField(
            model_name="comic",
            name="file_format",
            field=models.CharField(
                default="comic",
                max_length=5,
                validators=[codex.models.validate_file_format_choice],
            ),
        ),
    ]
