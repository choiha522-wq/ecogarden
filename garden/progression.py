from django.db import transaction
from django.db.models import F

from .models import GardenProgress

TIER_FIELDS = {1: 'easy_completed', 2: 'medium_completed', 3: 'hard_completed'}
TIER_LABELS = {1: '쉬움', 2: '보통', 3: '어려움'}
MAX_GRID_SIZE = 5


def tier_for_difficulty(difficulty):
    return max(1, min(3, int(difficulty or 1)))


def grid_size_for_level(level):
    return 3 if level <= 1 else 4 if level == 2 else MAX_GRID_SIZE


def plot_count_for_level(level):
    size = grid_size_for_level(level)
    return size * size


def unlocked_slot_indexes(size):
    """5칸 너비의 고정 슬롯 중 왼쪽 위 size×size 영역을 열어요."""
    return [row * MAX_GRID_SIZE + col for row in range(size) for col in range(size)]


def requirements_for_target_level(target_level):
    """해당 레벨에 도달하는 데 필요한 난이도별 누적 완성 개수."""
    required = {1: 0, 2: 0, 3: 0}
    for transition in range(1, max(1, target_level)):
        tier = (transition - 1) % 3 + 1
        required[tier] += transition + 2
    return required


def calculate_level(progress):
    counts = {1: progress.easy_completed, 2: progress.medium_completed, 3: progress.hard_completed}
    level = 1
    while True:
        required = requirements_for_target_level(level + 1)
        if all(counts[tier] >= amount for tier, amount in required.items()):
            level += 1
        else:
            return level


def record_completed_plants(user, difficulties):
    """완성된 식물 난이도를 누적하고 달성한 레벨을 즉시 반영해요."""
    increments = {1: 0, 2: 0, 3: 0}
    for difficulty in difficulties:
        increments[tier_for_difficulty(difficulty)] += 1
    with transaction.atomic():
        progress, _ = GardenProgress.objects.select_for_update().get_or_create(user=user)
        for tier, amount in increments.items():
            if amount:
                GardenProgress.objects.filter(pk=progress.pk).update(**{TIER_FIELDS[tier]: F(TIER_FIELDS[tier]) + amount})
        progress.refresh_from_db()
        next_level = calculate_level(progress)
        if next_level != progress.level:
            progress.level = next_level
            progress.save(update_fields=['level'])


def progress_payload(progress):
    """정원 화면에서 다음 레벨까지 필요한 난이도와 진행량을 보여줘요."""
    tier = (progress.level - 1) % 3 + 1
    field = TIER_FIELDS[tier]
    already_required = requirements_for_target_level(progress.level)[tier]
    target_count = progress.level + 2
    completed = max(0, getattr(progress, field) - already_required)
    return {
        'level': progress.level,
        'total_completed': progress.total_completed,
        'tier_completed': {
            'easy': progress.easy_completed,
            'medium': progress.medium_completed,
            'hard': progress.hard_completed,
        },
        'next_level': progress.level + 1,
        'required_tier': tier,
        'required_tier_label': TIER_LABELS[tier],
        'required_count': target_count,
        'progress_count': min(target_count, completed),
    }
