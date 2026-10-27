"""
시연/테스트용: 정원의 시간을 빨리 감기해요.

    python manage.py tick_garden --steps 30                  # 모든 사용자 정원을 30스텝 진행
    python manage.py tick_garden --steps 30 --username kim   # 특정 사용자만

한 스텝 = 게임 설정(GARDEN_STEP_MINUTES)의 시간이에요. 기본 10분이라 30스텝 = 5시간치 변화예요.
"""
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from garden import sim


class Command(BaseCommand):
    help = '정원 시뮬레이션을 지정한 스텝만큼 빨리 감기'

    def add_arguments(self, parser):
        parser.add_argument('--steps', type=int, required=True)
        parser.add_argument('--username')

    def handle(self, *args, **opts):
        users = User.objects.all()
        if opts['username']:
            users = users.filter(username=opts['username'])
            if not users.exists():
                raise CommandError('그 사용자를 찾을 수 없어요.')
        for u in users:
            sim.advance(u, steps=opts['steps'])
            u.refresh_from_db()
            self.stdout.write(f'{u.username}: {opts["steps"]}스텝 진행 → CO2 {u.co2_ppm:.1f}ppm')
