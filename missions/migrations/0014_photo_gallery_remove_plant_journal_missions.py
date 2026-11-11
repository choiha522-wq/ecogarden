from django.db import migrations, models


def deactivate_journal_missions(apps, schema_editor):
    Mission = apps.get_model('missions', 'Mission')
    Mission.objects.using(schema_editor.connection.alias).filter(mission_type='record').update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [('missions', '0013_biology_category_and_daily_rewards')]

    operations = [
        migrations.AddField(
            model_name='missionsubmission',
            name='photo_data',
            field=models.BinaryField(blank=True, editable=False, help_text='승인된 미션 사진을 압축해 개인 갤러리용으로 보관해요.', null=True),
        ),
        migrations.RunPython(deactivate_journal_missions, migrations.RunPython.noop),
    ]
