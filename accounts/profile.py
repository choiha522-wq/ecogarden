"""정원 레벨로 해금되는 칭호와 프로필 동물."""

PROFILE_TITLES = [
    (1, '초록정원 탐험가'),
    (2, '새싹 지킴이'),
    (3, '숲속 친구'),
    (4, '생물다양성 수호자'),
    (5, '숲길 탐험가'),
    (6, '생태계 관찰자'),
    (7, '서식지 지킴이'),
    (8, '숲 복원가'),
    (9, '생물다양성 전문가'),
    (10, '숲의 수호자'),
]

PROFILE_AVATARS = [
    (1, 'farmer', '🧑‍🌾', '정원사'),
    (2, 'bird', '🐦', '새'),
    (3, 'rabbit', '🐇', '토끼'),
    (4, 'deer', '🦌', '사슴'),
    (5, 'squirrel', '🐿️', '다람쥐'),
    (6, 'fox', '🦊', '여우'),
    (7, 'butterfly', '🦋', '나비'),
    (8, 'turtle', '🐢', '거북이'),
    (9, 'owl', '🦉', '부엉이'),
    (10, 'hedgehog', '🦔', '고슴도치'),
]


def garden_level(user):
    from garden.models import GardenProgress
    return GardenProgress.objects.filter(user_id=user.pk).values_list('level', flat=True).first() or 1


def title_options(level):
    return [{'title': title, 'unlock_level': required, 'unlocked': level >= required}
            for required, title in PROFILE_TITLES]


def avatar_options(level):
    return [{'key': key, 'emoji': emoji, 'name': name,
             'unlock_level': required, 'unlocked': level >= required}
            for required, key, emoji, name in PROFILE_AVATARS]


def avatar_emoji(key):
    return next((emoji for _, avatar_key, emoji, _ in PROFILE_AVATARS if avatar_key == key), '🧑‍🌾')
