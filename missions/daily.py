"""
매일 계정별로 달라지는 오늘의 미션.

- 활성 미션 풀에서 사진 2개 + 퀴즈 2개 + 관찰 기록 1개를 계정과 날짜별로 뽑아요.
- 같은 계정은 하루 동안 같은 미션을 보고, 다른 계정은 다른 조합을 받을 수 있어요.
- 문제가 하나도 없는 퀴즈는 뽑지 않아요.
"""
import random

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import DailyMission, Mission

DAILY_PHOTO = 2
DAILY_QUIZ = 2
DAILY_RECORD = 1


def _pick(day, user_id=0):
    pool = list(
        Mission.objects.filter(is_active=True)
        .annotate(nq=Count('questions'))
        .filter(Q(mission_type='photo') | Q(mission_type='quiz', nq__gt=0) | Q(mission_type='record'))
        .order_by('id')
    )
    # 기록형은 고정 식물 관찰일지만 사용해 미션 설명과 입력 폼이 항상 일치하게 해요.
    pool = [m for m in pool if m.mission_type != 'record' or m.title == '나의 식물 관찰일지']
    photos = [m for m in pool if m.mission_type == 'photo']
    quizzes = [m for m in pool if m.mission_type == 'quiz']
    records = [m for m in pool if m.mission_type == 'record']
    rng = random.Random(day.toordinal() * 1_000_003 + int(user_id or 0))
    picked = (rng.sample(photos, min(DAILY_PHOTO, len(photos)))
              + rng.sample(quizzes, min(DAILY_QUIZ, len(quizzes)))
              + rng.sample(records, min(DAILY_RECORD, len(records))))
    want = DAILY_PHOTO + DAILY_QUIZ + DAILY_RECORD
    if len(picked) < want:
        rest = [m for m in pool if m not in picked]
        picked += rng.sample(rest, min(want - len(picked), len(rest)))
    return sorted(picked, key=lambda m: m.id)


def ensure_daily(day=None, user=None, reroll=False):
    """계정의 오늘 미션을 없으면 생성하고 돌려줘요. 비로그인은 날짜별 미리보기만 제공해요."""
    day = day or timezone.localdate()
    user_id = user.pk if user is not None and getattr(user, 'is_authenticated', False) else 0
    picked = _pick(day, user_id)
    if user_id == 0:
        return Mission.objects.filter(pk__in=[m.pk for m in picked]).order_by('id')

    if reroll:
        DailyMission.objects.filter(date=day, user_id=user_id).delete()
    existing = DailyMission.objects.filter(date=day, user_id=user_id)
    if existing.exists() and set(existing.values_list('mission_id', flat=True)) != {m.id for m in picked}:
        existing.delete()
    for mission in picked:
        try:
            with transaction.atomic():
                DailyMission.objects.get_or_create(date=day, user_id=user_id, mission=mission)
        except IntegrityError:
            pass  # 같은 계정의 동시 요청에서 다른 요청이 먼저 만들었어요.
    return Mission.objects.filter(is_active=True, daily_entries__date=day,
                                  daily_entries__user_id=user_id).order_by('id').distinct()
