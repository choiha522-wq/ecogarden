from django.db import migrations, models


def copy_plant_names(apps, schema_editor):
    db = schema_editor.connection.alias
    Journal = apps.get_model('missions', 'ObservationJournal')
    for journal in Journal.objects.using(db).select_related('seed_type').iterator():
        Journal.objects.using(db).filter(pk=journal.pk).update(plant_name=journal.seed_type.name or '식물')


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0009_personal_daily_and_observation_journal'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationjournal',
            name='plant_name',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.RunPython(copy_plant_names, migrations.RunPython.noop),
        migrations.AddField(
            model_name='observationjournal',
            name='plant_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='observationjournal',
            name='plant_confirmed',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='observationjournal',
            name='plant_name',
            field=models.CharField(help_text='현실에서 키우는 식물 이름', max_length=80),
        ),
        migrations.RemoveField(
            model_name='observationjournal',
            name='seed_type',
        ),
    ]
