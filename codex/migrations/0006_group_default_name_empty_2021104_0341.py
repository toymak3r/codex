# Generated by Django 3.2.9 on 2021-11-04 03:03

from django.db import migrations, models
from django.db.models.functions import Now


MODEL_NAMES = {
    "Series": "Default Series",
    "Imprint": "Main Imprint",
    "Publisher": "No Publisher",
}
NEW_DEFAULT_NAME = ""


def update_default_names(apps, _schema_editor):
    """Prepare for removing the is_default field."""
    for model_name, default_name in MODEL_NAMES.items():
        model = apps.get_model("codex", model_name)
        model.objects.filter(name=NEW_DEFAULT_NAME, is_default=False).update(
            name="UNKNOWN", updated_at=Now()
        )
        model.objects.filter(name=default_name, is_default=True).update(
            name=NEW_DEFAULT_NAME, updated_at=Now()
        )


class Migration(migrations.Migration):

    dependencies = [
        ("codex", "0005_auto_20200918_0146"),
    ]

    operations = [
        migrations.RunPython(update_default_names),
        migrations.AlterField(
            model_name="publisher",
            name="name",
            field=models.CharField(db_index=True, default="", max_length=32),
        ),
        migrations.AlterField(
            model_name="imprint",
            name="name",
            field=models.CharField(db_index=True, default="", max_length=32),
        ),
        migrations.AlterField(
            model_name="series",
            name="name",
            field=models.CharField(db_index=True, default="", max_length=32),
        ),
        migrations.AlterField(
            model_name="volume",
            name="name",
            field=models.CharField(db_index=True, default="", max_length=32),
        ),
        migrations.AlterUniqueTogether(
            name="publisher",
            unique_together={("name",)},
        ),
        migrations.AlterUniqueTogether(
            name="imprint",
            unique_together={("name", "publisher")},
        ),
        migrations.AlterUniqueTogether(
            name="series",
            unique_together={("name", "imprint")},
        ),
        migrations.AlterUniqueTogether(
            name="volume",
            unique_together={("name", "series")},
        ),
        migrations.RemoveField(
            model_name="publisher",
            name="is_default",
        ),
        migrations.RemoveField(
            model_name="imprint",
            name="is_default",
        ),
        migrations.RemoveField(
            model_name="series",
            name="is_default",
        ),
        migrations.RemoveField(
            model_name="volume",
            name="is_default",
        ),
    ]
