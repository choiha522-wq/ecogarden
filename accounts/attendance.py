"""
출석 보상. 서버에 저장해서 같은 주 안에서 출석한 날짜 수가 이어져요.

- 월요일에 새 주가 시작되고 일요일까지 출석 횟수를 누적해요.
- 같은 주 안에서는 하루를 건너뛰어도 다음 출석 보상 단계가 이어져요.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

REWARDS = [10, 10, 15, 15, 20, 20, 50]   # 1~7일차 포인트 (7일차는 게임 티켓 1장도 같이)


def attendance_state(user):
    """지금 화면에 보여줄 출석 상태: {'streak': 이번 주기에서 출석한 날 수, 'claimed': 오늘 이미 받았는지}"""
    today = timezone.localdate()
    last, streak = user.attendance_date, user.attendance_streak
    if last == today:
        return {'streak': streak, 'claimed': True}
    week_start = today - timedelta(days=today.weekday())
    if last is not None and last >= week_start and streak < len(REWARDS):
        return {'streak': streak, 'claimed': False}
    return {'streak': 0, 'claimed': False}


def claim_attendance(user):
    """이번 주 출석 횟수에 따라 보상해요. 하루 한 번만 받을 수 있어요."""
    with transaction.atomic():
        locked = type(user).objects.select_for_update().get(pk=user.pk)
        state = attendance_state(locked)
        if state['claimed']:
            return None
        day = min(state['streak'] + 1, len(REWARDS))
        reward = REWARDS[day - 1]
        ticket = day == len(REWARDS)
        locked.points += reward
        if ticket:
            locked.tickets += 1
        locked.attendance_streak = day
        locked.attendance_date = timezone.localdate()
        locked.save(update_fields=['points', 'tickets', 'attendance_streak', 'attendance_date'])
        user.points, user.tickets = locked.points, locked.tickets
        user.attendance_streak, user.attendance_date = locked.attendance_streak, locked.attendance_date
        return {'day': day, 'reward': reward, 'ticket': ticket}
