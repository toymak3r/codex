"""Generated by Django 4.2.1 on 2023-05-17 19:22."""

import django.db.models.deletion
from django.db import migrations, models


def _create_story_arc_numbers(apps, _schema_editor):
    comic_model = apps.get_model("codex", "comic")
    san_model = apps.get_model("codex", "StoryArcNumber")
    num_sans = 0

    comics = comic_model.objects.exclude(story_arcs=None)
    print()
    print(f"Comics with story arcs: {comics.count()}")
    # Create a StoryArcNumber for each comic
    for comic in comics:
        sans = set()
        first_done = False
        for sa in comic.story_arcs.all():
            number = None if first_done else comic.story_arc_number
            kwargs = {"story_arc": sa, "number": number}
            san, created = san_model.objects.get_or_create(defaults=kwargs, **kwargs)
            num_sans += int(created)
            sans.add(san)
            first_done = True
        comic.story_arc_numbers.add(*sans)
        comic.save()

    num_sas = apps.get_model("codex", "StoryArc").objects.count()
    print(f"Created {num_sans} StoryArcNumbers for {num_sas} StoryArcs")


class Migration(migrations.Migration):
    """Run Migrations."""

    dependencies = [
        ("codex", "0024_comic_gtin_comic_story_arc_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="StoryArcNumber",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("number", models.PositiveIntegerField(default=None, null=True)),
                (
                    "story_arc",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="codex.storyarc",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="storyarcnumber",
            unique_together={("story_arc", "number")},
        ),
        migrations.AddField(
            model_name="comic",
            name="story_arc_numbers",
            field=models.ManyToManyField(to="codex.storyarcnumber"),
        ),
        migrations.RunPython(_create_story_arc_numbers),
        migrations.RemoveField(
            model_name="comic",
            name="story_arc_number",
        ),
        migrations.RemoveField(
            model_name="comic",
            name="story_arcs",
        ),
    ]
