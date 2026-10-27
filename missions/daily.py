"""
매일 바뀌는 오늘의 미션.

- 활성 미션 풀에서 사진 인증형 DAILY_PHOTO개 + 퀴즈형 DAILY_QUIZ개 + 기록형 DAILY_RECORD개를 날짜를 씨앗으로 뽑아요.
  (같은 날에는 모든 사용자가 같은 미션을 봐요. 풀이 넉넉할수록 매일 다양해져요.)
- 문제가 하나도 없는 퀴즈 미션은 뽑지 않아요.
- 완료했든 안 했든 자정(한국 시간)이 지나면 새 미션으로 바뀌고, 어제 푼 미션도 풀에 다시 들어가요.
"""
import random

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import DailyMission, Mission

DAILY_PHOTO = 2
DAILY_QUIZ = 2
DAILY_RECORD = 1


def _pick(day):
    pool = list(
        Mission.objects.filter(is_active=True)
        .annotate(nq=Count('questions'))
        .filter(Q(mission_type='photo') | Q(mission_type='quiz', nq__gt=0) | Q(mission_type='record'))
        .order_by('id')
    )
    photos = [m for m in pool if m.mission_type == 'photo']
    quizzes = [m for m in pool if m.mission_type == 'quiz']
    records = [m for m in pool if m.mission_type == 'record']
    rng = random.Random(day.toordinal())
    picked = (rng.sample(photos, min(DAILY_PHOTO, len(photos)))
              + rng.sample(quizzes, min(DAILY_QUIZ, len(quizzes)))
              + rng.sample(records, min(DAILY_RECORD, len(records))))
    want = DAILY_PHOTO + DAILY_QUIZ + DAILY_RECORD
    if len(picked) < want:  # 한쪽 종류가 모자라면 남은 풀에서 채워요
        rest = [m for m in pool if m not in picked]
        picked += rng.sample(rest, min(want - len(picked), len(rest)))
    return sorted(picked, key=lambda m: m.id)


def ensure_daily(day=None, reroll=False):
    """그날의 미션이 아직 없으면 뽑아서 저장하고, 오늘의 미션 목록을 돌려줘요."""
    day = day or timezone.localdate()
    if reroll:
        DailyMission.objects.filter(date=day).delete()
    existing = DailyMission.objects.filter(date=day)
    picked = _pick(day)
    if existing.exists() and set(existing.values_list('mission_id', flat=True)) != {m.id for m in picked}:
        existing.delete()  # 오늘 미션 비율이나 활성 미션 풀이 바뀌면 새 구성으로 다시 뽑아요.
    if not DailyMission.objects.filter(date=day).exists():
        for m in picked:
            try:
                with transaction.atomic():
                    DailyMission.objects.create(date=day, mission=m)
            except IntegrityError:  # 동시에 접속한 다른 요청이 먼저 만든 경우
                pass
    return Mission.objects.filter(is_active=True, daily_entries__date=day).order_by('id')
