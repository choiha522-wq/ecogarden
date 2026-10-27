"""
오늘의 미션 확인/다시 뽑기 (시연·테스트용).

    python manage.py daily_missions                       # 오늘의 미션 목록 보기
    python manage.py daily_missions --reroll              # 오늘의 미션을 다시 뽑기
    python manage.py daily_missions --date 2026-10-13     # 특정 날짜의 미션 미리 보기(없으면 새로 뽑아 저장)
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from missions.daily import ensure_daily


class Command(BaseCommand):
    help = '오늘의 미션을 보거나 다시 뽑아요'

    def add_arguments(self, parser):
        parser.add_argument('--reroll', action='store_true')
        parser.add_argument('--date')

    def handle(self, *args, **opts):
        day = date.fromisoformat(opts['date']) if opts['date'] else timezone.localdate()
        for m in ensure_daily(day, reroll=opts['reroll']):
            kind = {'quiz': '퀴즈', 'record': '관찰 기록'}.get(m.mission_type, '사진')
            self.stdout.write(f'{m.emoji} [{kind}] {m.title} (+{m.reward_points}P)')
        self.stdout.write(self.style.SUCCESS(f'{day} 미션 준비 완료'))
