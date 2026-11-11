from django.db import migrations


def unlock_easy_seeds_at_level_one(apps, schema_editor):
    SeedType = apps.get_model('garden', 'SeedType')
    SeedType.objects.using(schema_editor.connection.alias).filter(difficulty=1).update(unlock_level=1)


class Migration(migrations.Migration):
    dependencies = [('garden', '0008_expand_garden_to_7x7')]

    operations = [
        migrations.RunPython(unlock_easy_seeds_at_level_one, migrations.RunPython.noop),
    ]
