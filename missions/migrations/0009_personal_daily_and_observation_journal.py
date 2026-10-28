from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def clear_shared_daily_missions(apps, schema_editor):
    # 기존 오늘 목록은 모든 계정이 공유했던 임시 캐시이므로 새 사용자별로 다시 뽑아요.
    db = schema_editor.connection.alias
    apps.get_model('missions', 'DailyMission').objects.using(db).all().delete()
    apps.get_model('missions', 'Mission').objects.using(db).filter(
        mission_type='record', title__in=['그늘과 햇빛을 비교해요', '오늘 만난 생물 기록', '흙을 건강하게 하는 방법'],
    ).update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('garden', '0006_gardenplot_completion_recorded_seedtype_unlock_level_and_more'),
        ('missions', '0008_remove_mission_action_goal_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='dailymission',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='daily_missions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(clear_shared_daily_missions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='dailymission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='daily_missions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='dailymission',
            unique_together={('date', 'user', 'mission')},
        ),
        migrations.CreateModel(
            name='ObservationJournal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('seed_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                                related_name='observation_journals', to='garden.seedtype')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='observation_journal', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ObservationEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, default=django.utils.timezone.localdate)),
                ('response', models.CharField(max_length=500)),
                ('habitat', models.CharField(choices=[('garden', '정원/화분'), ('school', '학교'), ('park', '공원/화단'), ('forest', '숲'), ('other', '기타')], max_length=20)),
                ('sign', models.CharField(choices=[('leaf', '잎'), ('flower', '꽃'), ('fruit_seed', '열매/씨앗'), ('other', '기타')], max_length=20)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='entries', to='missions.observationjournal')),
            ],
            options={'ordering': ['-date', '-id']},
        ),
        migrations.AddConstraint(
            model_name='observationentry',
            constraint=models.UniqueConstraint(fields=('journal', 'date'), name='unique_daily_observation_entry'),
        ),
    ]
