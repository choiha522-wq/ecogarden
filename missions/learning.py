"""짧은 생태 학습 카드. 생성형 AI 실시간 생성 대신 고정된 기초 설명을 사용."""

QUIZ_CURRICULUM = {
    1: '생태계란 무엇인지 자신의 말로 설명해 보세요.',
    2: '생물 다양성이란 무엇이며, 왜 중요할까요?',
    3: '식물과 곤충은 생태계에서 어떤 관계를 맺고 있을까요?',
    4: '숲이 개발로 사라지면 그곳에 사는 생물들에게 어떤 영향이 생길까요?',
    5: '주변의 생태계 훼손 사례와 그 원인이 생태계에 미치는 영향을 설명해 보세요.',
    6: '종이 사용을 줄이는 행동은 산림 생태계 보호와 어떻게 연결될까요?',
    7: '특정 지역의 곤충 개체 수가 급격히 줄면 생태계에 어떤 변화가 생길까요?',
    8: '기후변화로 서식지가 줄어드는 생물을 보호할 대책을 생각해 보세요.',
    9: '학교 주변 생물 다양성을 높일 구체적인 생태계 보호 활동을 계획해 보세요.',
    10: '육상 생태계 파괴를 줄이기 위해 일상에서 할 행동을 정하고, 실천한 내용과 느낀 점을 돌아보세요.',
}

QUIZ_LEVEL_STEPS = [
    '계획하기: 내가 실천할 생태계 보호 행동을 정해요.',
    '실천하기: 정한 행동을 실제 생활에서 해 봐요.',
    '돌아보기: 실천한 내용과 느낀 점을 작성해요.',
]


def quiz_difficulty_for_level(level):
    level = max(1, min(10, int(level or 1)))
    if level <= 3:
        return 1, '하 · 초등학교 저학년 수준'
    if level <= 6:
        return 2, '중 · 초등학교 고학년 수준'
    if level <= 9:
        return 3, '상 · 중학교 수준'
    return 4, '최상 · 고등학교 수준'


def quiz_curriculum(level):
    level = max(1, min(10, int(level or 1)))
    difficulty, label = quiz_difficulty_for_level(level)
    result = {'level': level, 'difficulty': difficulty, 'difficulty_label': label,
              'focus': QUIZ_CURRICULUM[level]}
    if level == 10:
        result['steps'] = QUIZ_LEVEL_STEPS
    return result


def user_garden_level(user):
    from garden.models import GardenProgress
    return GardenProgress.objects.filter(user_id=user.pk).values_list('level', flat=True).first() or 1

def learning_card(mission):
    title = mission.title
    if any(word in title for word in ('낙엽', '미생물', '흙', '지렁이')):
        return {'title': '낙엽과 흙 속 분해자', 'text': '곰팡이와 세균 같은 분해자는 낙엽 등 유기물을 분해해요. 이 과정은 양분이 생태계 안에서 다시 순환하는 데 도움을 줘요. 화단의 낙엽과 작은 생물을 함부로 걷어내지 말고 관찰해 보세요.', 'action': '안전한 산책길에서 낙엽이 있는 흙과 없는 흙의 모습을 비교해 보세요.'}
    if any(word in title for word in ('꽃', '벌', '나비', '곤충')):
        return {'title': '꽃과 곤충은 서로 연결돼요', 'text': '꽃을 찾는 일부 곤충은 꽃가루를 다른 꽃으로 옮겨 식물의 번식을 도와요. 다양한 꽃이 있는 공간은 곤충의 먹이와 쉼터가 될 수 있어요. 곤충은 잡지 말고 멀리서 살펴봐요.', 'action': '꽃에 곤충이 방문하는지 잠시 조용히 관찰해 보세요.'}
    if any(word in title for word in ('탄소', '나무', '숲', '햇빛')):
        return {'title': '식물과 탄소의 순환', 'text': '식물은 빛을 이용하는 광합성으로 이산화탄소와 물에서 양분을 만들어요. 탄소 일부는 줄기와 뿌리 등에 저장돼요. 나무를 심는 것뿐 아니라 기존 식물과 토양을 잘 보전하는 것도 중요해요.', 'action': '집이나 학교의 식물을 해치지 않고 돌볼 방법 한 가지를 정해 보세요.'}
    return {'title': '작은 관찰이 환경 실천의 시작이에요', 'text': '잎, 꽃, 흙의 변화를 같은 장소에서 꾸준히 기록하면 생물이 주변 환경과 어떻게 관계를 맺는지 생각해 볼 수 있어요. 생물을 함부로 만지거나 꺾지 않고 관찰하는 것도 생태계를 지키는 실천이에요.', 'action': '다음 관찰 때 오늘과 달라진 점 한 가지를 찾아보세요.'}
