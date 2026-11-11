from django.db import migrations, models
from django.db.models import F


def update_existing_missions(apps, schema_editor):
    Mission = apps.get_model('missions', 'Mission')
    QuizHistory = apps.get_model('missions', 'QuizHistory')
    alias = schema_editor.connection.alias
    Mission.objects.using(alias).filter(category='local').update(category='biology')
    Mission.objects.using(alias).filter(title='지역 환경 퀴즈').update(
        title='생물과 생태계 퀴즈', description='생물의 특징과 생태계 안의 관계를 알아보는 퀴즈예요.',
    )
    Mission.objects.using(alias).filter(title='탄소와 우리 동네 나무').update(
        title='식물과 탄소 순환', description='식물과 생태계의 탄소 순환을 알아보는 퀴즈예요.',
    )
    Mission.objects.using(alias).filter(title='도시 숲 탐험하기', category='biology').update(
        description='숲에서 서로 다른 나무와 주변 식물을 관찰하고, 큰 나무를 찍어요.',
    )
    Mission.objects.using(alias).update(reward_points=F('reward_points') + 10)
    QuizHistory.objects.using(alias).filter(category='local').update(category='biology')


def reverse_existing_missions(apps, schema_editor):
    Mission = apps.get_model('missions', 'Mission')
    QuizHistory = apps.get_model('missions', 'QuizHistory')
    alias = schema_editor.connection.alias
    Mission.objects.using(alias).filter(category='biology').update(category='local')
    Mission.objects.using(alias).filter(title='생물과 생태계 퀴즈').update(title='지역 환경 퀴즈')
    Mission.objects.using(alias).filter(title='식물과 탄소 순환').update(title='탄소와 우리 동네 나무')
    Mission.objects.using(alias).update(reward_points=F('reward_points') - 10)
    QuizHistory.objects.using(alias).filter(category='biology').update(category='local')


class Migration(migrations.Migration):
    dependencies = [('missions', '0012_expand_quiz_bank')]

    operations = [
        migrations.RunPython(update_existing_missions, reverse_existing_missions),
        migrations.AlterField(
            model_name='mission',
            name='category',
            field=models.CharField(
                choices=[('observation', '관찰'), ('microbe', '미생물'), ('biology', '생물')],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='mission',
            name='reward_points',
            field=models.PositiveIntegerField(default=30),
        ),
    ]
