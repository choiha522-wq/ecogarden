from django.core.management.base import BaseCommand

from garden.models import SeedType
from garden.species_data import SPECIES
from missions.models import Mission, QuizQuestion
from shop.models import ShopItem

# (카테고리, 제목, 이모지, 설명, 포인트, AI검증, 종류)
MISSIONS = [
    # --- 사진 인증형 (안전하게, 만지거나 꺾지 않고 멀리서 관찰해요) ---
    ('observation', '우리 동네 식물 3종 찍기', '📸', '공원이나 화단에서 서로 다른 식물 3종류를 찍으면 AI가 이름을 알려줘요.', 40, True, 'photo'),
    ('observation', '곤충 한 마리 발견하기', '🐝', '꽃 근처를 살펴보세요. 만지지 말고 멀리서 찍어요.', 40, False, 'photo'),
    ('biology', '도시 숲 탐험하기', '🌳', '숲에서 서로 다른 나무와 주변 식물을 관찰하고, 큰 나무를 찍어요.', 50, False, 'photo'),
    ('observation', '잎맥이 보이는 나뭇잎 찾기', '🍃', '살아있는 잎은 뜯지 말고, 떨어진 잎이나 잎 뒷면의 줄무늬(잎맥)가 잘 보이게 찍어요.', 40, True, 'photo'),
    ('observation', '이끼 발견하기', '🌿', '그늘지고 촉촉한 곳의 이끼를 찾아보세요. 만지지 말고 가까이에서 살짝 찍어요.', 40, True, 'photo'),
    ('observation', '꽃에 앉은 벌이나 나비 찾기', '🦋', '꽃에 온 벌이나 나비를 멀리서 조용히 찍어요. 손으로 잡으면 안 돼요.', 50, True, 'photo'),
    ('observation', '떨어진 낙엽 3종류 찍기', '🍂', '서로 다른 모양의 낙엽을 한곳에 모아 한 장에 담아 찍어요.', 40, True, 'photo'),
    ('microbe', '화단 흙 관찰하기', '🪱', '화단이나 화분의 흙을 가까이에서 찍어요. 색깔, 알갱이, 작은 생물이 있는지 살펴봐요.', 40, False, 'photo'),
    ('biology', '나무 열매나 씨앗 찾기', '🌰', '나무에 달린 열매나 땅에 떨어진 씨앗을 찾아 찍어요. 먹지는 않아요!', 40, True, 'photo'),
    ('biology', '그늘과 햇빛 비교하기', '☀️', '같은 식물이 그늘과 햇빛에서 잎의 모양이나 색이 어떻게 다른지 찍어요.', 40, False, 'photo'),
    ('biology', '학교 화단 새싹 찾기', '🌱', '화단이나 화분에서 막 올라온 새싹을 찾아 찍어요.', 40, True, 'photo'),
    ('observation', '내 키보다 큰 나무 찾기', '🌲', '나무 옆에서 나무 전체가 보이도록 멀리서 찍어요. 나무에 올라가면 안 돼요.', 40, True, 'photo'),
    # --- 퀴즈형 ---
    ('microbe', '낙엽은 어떻게 사라질까?', '🦠', '낙엽 분해 과정을 배우고 퀴즈를 풀어요.', 30, False, 'quiz'),
    ('microbe', '흙 속 미생물 퀴즈', '🧫', '미생물과 식물의 관계를 알아봐요.', 30, False, 'quiz'),
    ('observation', '꽃과 곤충의 관계', '🌼', '꽃가루받이가 무엇인지 알아보는 퀴즈예요.', 30, False, 'quiz'),
    ('observation', '나무가 하는 일', '🌳', '나무의 광합성과 탄소 흡수를 알아보는 퀴즈예요.', 30, False, 'quiz'),
    ('biology', '숲속 먹이사슬', '🐿️', '생산자, 소비자, 분해자의 관계를 알아보는 퀴즈예요.', 30, False, 'quiz'),
    ('biology', '생물다양성이란?', '🌈', '다양한 생물이 서로 어떤 영향을 주고받는지 알아봐요.', 30, False, 'quiz'),
    ('microbe', '흙 속 친구, 지렁이', '🪱', '지렁이가 흙을 어떻게 건강하게 만드는지 알아봐요.', 30, False, 'quiz'),
    ('biology', '식물과 탄소 순환', '🌍', '식물과 생태계의 탄소 순환을 알아보는 퀴즈예요.', 30, False, 'quiz'),
]

# 제목 -> [(문제, [보기...], 정답번호(1부터), 해설)]
QUIZZES = {
    '낙엽은 어떻게 사라질까?': [
        ('땅에 떨어진 낙엽을 잘게 분해해서 흙으로 돌려보내는 생물은?',
         ['곰팡이와 세균', '나비', '참새', '거미'], 1,
         '곰팡이와 세균 같은 분해자가 낙엽을 분해해서 영양분을 흙으로 돌려보내요.'),
        ('낙엽이 분해되면 흙에는 무엇이 늘어날까?',
         ['식물이 자라는 데 필요한 영양분', '플라스틱', '소금', '모래'], 1,
         '분해된 낙엽은 영양분이 되어 식물이 자라는 데 쓰여요.'),
        ('낙엽이 가장 빨리 분해되는 날씨는?',
         ['따뜻하고 촉촉할 때', '아주 춥고 건조할 때', '꽁꽁 얼어 있을 때', '바싹 말라 있을 때'], 1,
         '미생물은 따뜻하고 촉촉한 곳에서 가장 활발하게 활동해요.'),
    ],
    '흙 속 미생물 퀴즈': [
        ('눈에 보이지 않을 만큼 아주 작은 흙 속 생물을 무엇이라고 부를까?',
         ['미생물', '대형 동물', '곤충', '새'], 1,
         '현미경으로 봐야 보일 만큼 작은 생물을 미생물이라고 해요.'),
        ('비 온 뒤 나는 흙냄새를 만드는 데 관여하는 미생물은?',
         ['방선균', '꿀벌', '무당벌레', '잠자리'], 1,
         '흙 속 방선균이 만드는 물질이 비 온 뒤 흙냄새의 원인이에요.'),
        ('미생물이 많은 건강한 흙의 모습은?',
         ['식물이 잘 자라는 부드러운 흙', '아주 딱딱하게 굳은 흙', '돌만 가득한 흙', '물이 전혀 없는 흙'], 1,
         '미생물이 많으면 흙이 부드러워지고 식물이 튼튼하게 자라요.'),
    ],
    '꽃과 곤충의 관계': [
        ('꽃가루를 옮겨 주며 꽃이 열매를 맺도록 도와주는 곤충은?',
         ['벌과 나비', '지렁이', '달팽이', '거미'], 1,
         '벌과 나비는 꿀을 먹으러 꽃에 앉았다가 꽃가루를 다른 꽃으로 옮겨 줘요.'),
        ('꽃이 향기롭고 색이 화려한 까닭으로 가장 알맞은 것은?',
         ['곤충을 불러서 꽃가루받이를 하려고', '사람에게 보이려고', '비를 피하려고', '땅속 물을 찾으려고'], 1,
         '화려한 색과 향기는 벌과 나비 같은 곤충을 불러 모으는 신호예요.'),
        ('꽃가루받이가 끝난 꽃은 보통 무엇이 될까?',
         ['열매와 씨앗', '뿌리', '줄기', '낙엽'], 1,
         '꽃가루받이가 되면 꽃이 지고 그 자리에 열매와 씨앗이 생겨요.'),
    ],
    '나무가 하는 일': [
        ('나무가 광합성을 할 때 공기 중에서 흡수하는 기체는?',
         ['이산화탄소', '헬륨', '수소', '네온'], 1,
         '나무는 공기 중의 이산화탄소를 흡수해서 양분을 만들어요.'),
        ('나무가 광합성을 하면서 공기 중으로 내보내는 기체는?',
         ['산소', '이산화탄소', '메탄', '연기'], 1,
         '광합성을 하면 산소가 만들어져서 공기 중으로 나와요.'),
        ('광합성에 꼭 필요한 것은 햇빛, 이산화탄소 그리고 무엇일까?',
         ['물', '소금', '기름', '철가루'], 1,
         '식물은 뿌리로 빨아들인 물과 햇빛, 이산화탄소로 양분을 만들어요.'),
    ],
    '숲속 먹이사슬': [
        ('먹이사슬에서 햇빛으로 스스로 양분을 만드는 생물은?',
         ['식물', '토끼', '매', '뱀'], 1,
         '식물은 광합성으로 스스로 양분을 만들어서 먹이사슬의 시작이 돼요.'),
        ('"식물 → 메뚜기 → 개구리 → 뱀"에서 메뚜기가 먹는 것은?',
         ['식물', '개구리', '뱀', '흙'], 1,
         '화살표는 먹히는 쪽에서 먹는 쪽으로 가요. 메뚜기는 식물을 먹어요.'),
        ('죽은 생물이나 낙엽을 분해해서 흙으로 돌려보내는 것은?',
         ['분해자(곰팡이·세균 등)', '태양', '바람', '구름'], 1,
         '곰팡이와 세균 같은 분해자가 죽은 생물을 분해해서 영양분을 흙으로 돌려보내요.'),
    ],
    '생물다양성이란?': [
        ('생물다양성이 높은 숲의 모습은?',
         ['여러 종류의 식물과 동물이 함께 살아요', '한 가지 나무만 가득해요', '동물이 하나도 없어요', '같은 종류의 곤충만 살아요'], 1,
         '생물다양성은 여러 종류의 생물이 함께 어울려 사는 것을 말해요.'),
        ('도시에서 생물다양성을 높이는 방법으로 알맞은 것은?',
         ['화단에 여러 종류의 꽃과 나무 심기', '모든 풀을 뽑고 시멘트로 덮기', '농약을 많이 뿌리기', '나무를 모두 베어내기'], 1,
         '여러 종류의 식물이 있으면 곤충과 새도 다양하게 찾아와요.'),
        ('벌과 나비가 줄어들면 식물에게 생기는 문제는?',
         ['꽃가루받이가 어려워져 열매와 씨앗이 줄어요', '잎이 더 커져요', '뿌리가 길어져요', '물이 필요 없어져요'], 1,
         '벌과 나비가 줄면 꽃가루받이가 잘 안 되어 열매와 씨앗이 줄어들어요.'),
    ],
    '흙 속 친구, 지렁이': [
        ('지렁이가 흙 속을 돌아다니면 흙은 어떻게 될까?',
         ['공기가 잘 통하고 부드러워져요', '딱딱하게 굳어요', '소금이 생겨요', '물이 모두 사라져요'], 1,
         '지렁이가 다니는 길로 공기와 물이 잘 통해서 흙이 부드러워져요.'),
        ('지렁이가 낙엽과 흙을 먹고 눈 똥(분변토)은 흙에 무엇을 더해 줄까?',
         ['식물이 쓸 수 있는 영양분', '플라스틱', '독', '모래 알갱이만'], 1,
         '지렁이의 똥은 식물에게 좋은 영양분이 되어 흙을 기름지게 해요.'),
        ('지렁이가 좋아하는 곳은?',
         ['촉촉하고 어두운 흙', '뜨겁고 바싹 마른 모래', '햇볕이 쨍쨍한 아스팔트', '얼음 위'], 1,
         '지렁이는 피부로 숨을 쉬어서 촉촉하고 어두운 흙을 좋아해요.'),
    ],
    '식물과 탄소 순환': [
        ('공기 중 이산화탄소가 너무 많아지면 지구에는 어떤 일이 생길까?',
         ['지구가 점점 더워져요', '지구가 점점 얼어요', '달이 커져요', '바다가 사라져요'], 1,
         '이산화탄소는 지구의 열을 가두는 온실가스라서 많아지면 지구가 더워져요.'),
        ('이산화탄소를 줄이는 데 도움이 되는 행동은?',
         ['나무를 심고 가꾸기', '쓰레기 태우기', '안 쓰는 전등 켜 두기', '일회용품 많이 쓰기'], 1,
         '나무는 이산화탄소를 흡수하고, 에너지와 쓰레기를 아끼면 배출도 줄어요.'),
        ('숲이 사라지면 어떤 일이 생길까?',
         ['이산화탄소를 흡수할 나무가 줄어요', '공기가 더 맑아져요', '동물이 늘어나요', '흙이 더 기름져요'], 1,
         '나무가 줄어들면 이산화탄소를 흡수하는 힘이 약해지고 동물의 보금자리도 사라져요.'),
    ],
}


class Command(BaseCommand):
    help = '나무·꽃 씨앗 40여 종, 미션, 퀴즈, 상점 데이터를 생성/갱신합니다 (중복 실행해도 안전).'

    def handle(self, *args, **options):
        # 나무·꽃 씨앗 (garden/species_data.py). 다시 실행하면 종 정보는 최신으로 갱신되지만,
        # 상점 가격은 이미 있는 항목이면 그대로 둬요.
        for sp in SPECIES:
            fields = {k: v for k, v in sp.items() if k != 'key'}
            seed, _ = SeedType.objects.update_or_create(key=sp['key'], defaults=fields)
            item, created = ShopItem.objects.get_or_create(
                item_type='seed', seed_type=seed,
                defaults=dict(name=f"{sp['name']} 씨앗", emoji=sp['emoji'],
                              description=sp['description'], price=sp['price']),
            )
            if not created:
                item.name, item.emoji, item.description = f"{sp['name']} 씨앗", sp['emoji'], sp['description']
                item.save(update_fields=['name', 'emoji', 'description'])

        Mission.objects.filter(title__in=['그늘과 햇빛을 비교해요', '오늘 만난 생물 기록', '흙을 건강하게 하는 방법'], mission_type='record').update(is_active=False)

        for category, title, emoji, desc, points, ai, mtype in MISSIONS:
            mission, created = Mission.objects.get_or_create(
                title=title,
                defaults=dict(
                    description=desc, category=category, emoji=emoji, mission_type=mtype,
                    reward_points=points, reward_tickets=1,
                    requires_photo=(mtype == 'photo'), ai_assisted=ai,
                ),
            )
            # 예전에 만들어진 미션이면 종류만 맞춰줌
            # 보상 물방울/햇빛 조각: 사진은 💧1 + ☀️1, 퀴즈·기록은 💧2.
            # (관리자가 따로 바꾼 미션은 건드리지 않아요)
            want = (1, 1) if mtype == 'photo' else (2, 0)
            if created or (mission.reward_water, mission.reward_sunlight) == (1, 0):
                mission.reward_water, mission.reward_sunlight = want
                mission.save(update_fields=['reward_water', 'reward_sunlight'])
            type_changed = mission.mission_type != mtype
            if type_changed:
                mission.mission_type = mtype
                mission.requires_photo = (mtype == 'photo')
            if type_changed:
                mission.save()

            if mtype == 'quiz' and not mission.questions.exists():
                for i, (text, choices, answer, expl) in enumerate(QUIZZES.get(title, [])):
                    c = choices + [''] * (4 - len(choices))
                    QuizQuestion.objects.create(
                        mission=mission, order=i, text=text,
                        choice1=c[0], choice2=c[1], choice3=c[2], choice4=c[3],
                        answer=answer, explanation=expl,
                    )

        ShopItem.objects.get_or_create(
            item_type='nutrient', name='영양제', emoji='🧪',
            defaults=dict(description='흙의 영양분을 채워요', price=20),
        )
        ShopItem.objects.filter(item_type='nutrient').update(description='흙의 영양분을 채워요')
        ShopItem.objects.get_or_create(
            item_type='microbe', name='미생물제', emoji='🦠',
            defaults=dict(description='흙 속 미생물이 늘어 나무가 더 빨리 자라요', price=25),
        )
        ShopItem.objects.get_or_create(
            item_type='water', name='물방울 5개', emoji='💧',
            defaults=dict(description='나무에 물을 줄 수 있어요 (30분마다 1개씩 저절로도 모여요)', price=10, quantity=5),
        )
        ShopItem.objects.get_or_create(
            item_type='sunlight', name='햇빛 조각', emoji='☀️',
            defaults=dict(description='그늘진 칸에 햇빛을 채워줘요', price=15, quantity=1),
        )
        ShopItem.objects.get_or_create(
            item_type='ticket', name='게임 티켓', emoji='🎟️',
            defaults=dict(description='미니게임 1회', price=40),
        )

        Mission.objects.filter(mission_type='record').update(is_active=False)
        self.stdout.write(self.style.SUCCESS('데모 데이터 생성 완료'))


        from garden.unlocks import assign_unlock_levels
        assign_unlock_levels(SeedType)
