from django.db import migrations


def create_record_missions(apps, schema_editor):
    Mission = apps.get_model('missions', 'Mission')
    records = [
        ('그늘과 햇빛을 비교해요', '☀️', '집이나 학교 주변에서 그늘과 햇빛이 드는 곳을 살펴보고, 그곳의 온도나 식물 모습 차이를 두 문장으로 적어요.', 'local'),
        ('오늘 만난 생물 기록', '📝', '오늘 본 식물이나 곤충 한 가지를 떠올려 어디에서 보았는지와 어떤 점이 눈에 띄었는지 적어요.', 'observation'),
        ('흙을 건강하게 하는 방법', '🪱', '식물 주변의 흙을 관찰하고 흙을 건강하게 지키는 방법이나 궁금한 점을 두 문장으로 적어요.', 'microbe'),
    ]
    for title, emoji, description, category in records:
        Mission.objects.get_or_create(title=title, defaults={
            'description': description, 'category': category, 'mission_type': 'record',
            'emoji': emoji, 'reward_points': 25, 'reward_tickets': 1,
            'reward_water': 2, 'reward_sunlight': 0, 'requires_photo': False,
            'ai_assisted': False, 'is_active': True,
        })


class Migration(migrations.Migration):
    dependencies = [('missions', '0004_mission_reward_sunlight_mission_reward_water')]
    operations = [migrations.RunPython(create_record_missions, migrations.RunPython.noop)]
