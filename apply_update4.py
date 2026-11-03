#!/usr/bin/env python3
"""
update4 패치 — 출석 서버 저장 / 물방울·햇빛 조각 / AI가 알아보는 사진 식물 심기

사용법 (manage.py가 있는 ecogarden 폴더에서):
    python apply_update4.py

- 바꿀 부분만 찾아서 고쳐요. 하나라도 못 찾으면 어디가 안 맞는지 알려주고, 아무 파일도 고치지 않아요.
- 이미 적용된 곳은 건너뛰어요 (여러 번 실행해도 안전해요).
- 고치기 전의 원본은 .update4_backup/ 폴더에 복사해 둬요.
- 끝나면 안내대로 makemigrations / migrate / seed_demo_data 를 실행하세요.
"""
import os
import re
import shutil
import sys

FAIL, DONE = [], []
BACKUP = '.update4_backup'
PENDING = {}   # 메모리에서 먼저 모두 고쳐보고, 하나도 실패하지 않았을 때만 한꺼번에 파일에 써요


def cur(path):
    if path in PENDING:
        return PENDING[path]
    if os.path.exists(path):
        return open(path, encoding='utf-8').read()
    return None


def wr(path, text):
    PENDING[path] = text


def _need(path):
    s = cur(path)
    if s is None:
        msg = f'{path} — 파일이 없어요 (manage.py가 있는 폴더에서 실행했는지 확인해 주세요)'
        if msg not in FAIL:
            FAIL.append(msg)
    return s


def flush():
    for path, text in PENDING.items():
        if os.path.exists(path):
            if open(path, encoding='utf-8').read() == text:
                continue
            dst = os.path.join(BACKUP, path)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(path, dst)
        else:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        open(path, 'w', encoding='utf-8').write(text)


def patch(path, old, new, done):
    """old 문장을 new로 바꿔요. done이 이미 들어있으면 적용된 걸로 보고 건너뛰어요."""
    s = _need(path)
    if s is None:
        return
    if done in s:
        DONE.append(f'이미 적용됨  {path}')
    elif old not in s:
        FAIL.append(f'{path} — 바꿀 부분을 못 찾았어요: {old.strip()[:70]!r}')
    else:
        wr(path, s.replace(old, new, 1))
        DONE.append(f'수정          {path}')


def insert_after(path, line_regex, text, done):
    """정규식에 맞는 줄 바로 다음에 text를 끼워 넣어요."""
    s = _need(path)
    if s is None:
        return
    if done in s:
        DONE.append(f'이미 적용됨  {path}')
        return
    m = re.search(line_regex, s, flags=re.M)
    if not m:
        FAIL.append(f'{path} — 끼워 넣을 위치를 못 찾았어요: {line_regex[:60]!r}')
        return
    wr(path, s[:m.end()] + text + s[m.end():])
    DONE.append(f'수정          {path}')


def replace_line(path, line_regex, new_line, done):
    s = _need(path)
    if s is None:
        return
    if done in s:
        DONE.append(f'이미 적용됨  {path}')
        return
    m = re.search(line_regex, s, flags=re.M)
    if not m:
        FAIL.append(f'{path} — 바꿀 줄을 못 찾았어요: {line_regex[:60]!r}')
        return
    wr(path, s[:m.start()] + new_line + s[m.end():])
    DONE.append(f'수정          {path}')


def replace_range(path, start, end, new, done):
    """start 문장부터 end 문장 직전(end가 None이면 파일 끝)까지를 new로 바꿔요."""
    s = _need(path)
    if s is None:
        return
    if done in s:
        DONE.append(f'이미 적용됨  {path}')
        return
    i = s.find(start)
    if i < 0:
        FAIL.append(f'{path} — 바꿀 구간의 시작을 못 찾았어요: {start.strip()[:60]!r}')
        return
    j = len(s) if end is None else s.find(end, i + 1)
    if j < 0:
        FAIL.append(f'{path} — 바꿀 구간의 끝을 못 찾았어요: {end.strip()[:60]!r}')
        return
    wr(path, s[:i] + new + s[j:])
    DONE.append(f'수정          {path}')


def append_end(path, text, done):
    s = _need(path)
    if s is None:
        return
    if done in s:
        DONE.append(f'이미 적용됨  {path}')
        return
    wr(path, s.rstrip('\n') + '\n' + text)
    DONE.append(f'수정          {path}')


def new_file(path, text):
    if cur(path) == text:
        DONE.append(f'이미 적용됨  {path}')
        return
    wr(path, text)
    DONE.append(f'새 파일       {path}')


if not os.path.exists('manage.py'):
    sys.exit('manage.py가 있는 폴더(ecogarden)에서 실행해 주세요.')

# =====================================================================
# 새 파일
# =====================================================================
new_file('accounts/attendance.py', r'''"""
출석 보상. 서버에 저장해서 다음 날 접속해도 연속 출석이 이어져요.

- 어제 출석했으면 오늘 출석하면 연속 +1 (1일 → 2일 → ... → 7일)
- 하루라도 빠지면 다시 1일차부터 시작해요.
- 7일차를 받으면 그다음 날은 다시 1일차예요 (7일 주기).
"""
from datetime import timedelta

from django.utils import timezone

REWARDS = [10, 10, 15, 15, 20, 20, 50]   # 1~7일차 포인트 (7일차는 게임 티켓 1장도 같이)


def attendance_state(user):
    """지금 화면에 보여줄 출석 상태: {'streak': 이번 주기에서 출석한 날 수, 'claimed': 오늘 이미 받았는지}"""
    today = timezone.localdate()
    last, streak = user.attendance_date, user.attendance_streak
    if last == today:
        return {'streak': streak, 'claimed': True}
    if last == today - timedelta(days=1) and streak < len(REWARDS):
        return {'streak': streak, 'claimed': False}
    return {'streak': 0, 'claimed': False}   # 하루 이상 빠졌거나, 7일을 다 채운 다음 날


def claim_attendance(user):
    """오늘 출석 보상을 지급해요. 이미 받았으면 None."""
    state = attendance_state(user)
    if state['claimed']:
        return None
    day = state['streak'] + 1
    reward = REWARDS[day - 1]
    ticket = day == len(REWARDS)
    user.points += reward
    if ticket:
        user.tickets += 1
    user.attendance_streak = day
    user.attendance_date = timezone.localdate()
    user.save(update_fields=['points', 'tickets', 'attendance_streak', 'attendance_date'])
    return {'day': day, 'reward': reward, 'ticket': ticket}
''')

new_file('garden/ai.py', r'''"""
사진 속 식물이 어떤 종인지 AI(Gemini)로 알아보는 기능.

우리 게임에 있는 식물 목록(나무·꽃 41종) 중에서 "같은 종" 또는 "가장 비슷한 종"을 골라요.
(목록에 없는 식물이면 가장 비슷한 종으로 심고, 식물이 아니면 거절해요.)
"""
import json

from django.conf import settings

from missions.services import _generate

from .models import SeedType


class AIUnavailable(Exception):
    """GEMINI_API_KEY가 없어서 AI를 쓸 수 없을 때."""


def identify_plant(image_bytes):
    """
    image_bytes: JPEG로 줄인 사진 데이터
    반환: {'is_plant': bool, 'species_key': str|None, 'match': 'exact'|'similar'|'none', 'label': str, 'reason': str}
    """
    if not settings.GEMINI_API_KEY:
        raise AIUnavailable()

    from google.genai import types

    catalog = '\n'.join(
        f"- {s.key}: {s.name} ({'나무' if s.kind == 'tree' else '꽃'})"
        for s in SeedType.objects.order_by('kind', 'id')
    )
    prompt = f"""너는 어린이용 생태 교육 게임의 식물 판별 AI야.
사진 속 식물이 아래 [목록] 중 어떤 종인지 골라줘.

[목록]
{catalog}

[규칙]
- species_key에는 반드시 [목록]에 있는 key만 써. 목록에 없는 이름을 만들지 마.
- 사진에 나무, 꽃, 풀 같은 식물이 뚜렷하게 있으면 is_plant를 true로 해.
- 목록의 종과 정확히 같으면 match를 "exact", 목록에서 가장 비슷한 종을 골랐으면 "similar"로 해.
- 식물이 없거나 사람, 동물, 음식, 물건, 화면 캡처뿐이면 is_plant를 false, species_key를 null, match를 "none"으로 해.
- label에는 사진 속 식물의 실제 이름을 한글로 써 (모르면 "알 수 없는 식물"). 사람이나 개인정보는 언급하지 마.
- reason은 어린이가 이해할 쉬운 말 한 문장으로 써.

아래 JSON 형식으로만 답해.
{{"is_plant": true, "species_key": "oak", "match": "exact", "label": "참나무", "reason": "잎이 넓고 가장자리가 물결 모양이라 참나무 같아요."}}"""

    resp = _generate([types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), prompt])
    text = (resp.text or '').strip().strip('`')
    if text.lower().startswith('json'):
        text = text[4:].strip()
    data = json.loads(text)
    return {
        'is_plant': bool(data.get('is_plant')),
        'species_key': data.get('species_key') or None,
        'match': str(data.get('match', 'none')),
        'label': str(data.get('label', ''))[:40],
        'reason': str(data.get('reason', ''))[:200],
    }
''')

# =====================================================================
# accounts
# =====================================================================
insert_after('accounts/models.py', r'^    microbes = models\.PositiveIntegerField\(default=0\).*\n',
             "    water_drops = models.PositiveIntegerField(default=5)   # 보유한 물방울 (물 주기에 1개씩 써요)\n"
             "    water_refill_at = models.DateTimeField(null=True, blank=True)  # 다음 물방울이 모이기 시작한 시각\n"
             "    sunlight = models.PositiveIntegerField(default=1)      # 보유한 햇빛 조각 (햇빛 주기에 1개씩 써요)\n",
             'water_drops = models.PositiveIntegerField')
insert_after('accounts/models.py', r'^    garden_updated_at = models\.DateTimeField\(null=True, blank=True\).*\n',
             "\n    # --- 출석 (서버에 저장해요) ---\n"
             "    attendance_streak = models.PositiveSmallIntegerField(default=0)   # 이번 7일 주기에서 출석한 날 수\n"
             "    attendance_date = models.DateField(null=True, blank=True)         # 마지막으로 출석한 날\n"
             "\n    # --- 사진으로 식물 심기: 하루 횟수 제한 ---\n"
             "    photo_plant_date = models.DateField(null=True, blank=True)\n"
             "    photo_plant_count = models.PositiveSmallIntegerField(default=0)\n",
             'attendance_streak = models.PositiveSmallIntegerField')

patch('accounts/serializers.py', "from .models import User\n", "from .attendance import attendance_state\nfrom .models import User\n",
      'from .attendance import attendance_state')
replace_range('accounts/serializers.py', 'class UserSerializer(serializers.ModelSerializer):', 'class ProfileUpdateSerializer',
              '''class UserSerializer(serializers.ModelSerializer):
    attendance_streak = serializers.SerializerMethodField()
    attendance_claimed_today = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'points', 'tickets', 'nutrients', 'microbes', 'water_drops', 'sunlight',
            'friend_code', 'region_sido', 'region_sigungu', 'school_level', 'date_joined',
            'attendance_streak', 'attendance_claimed_today',
        )
        read_only_fields = fields

    def get_attendance_streak(self, obj):
        return attendance_state(obj)['streak']

    def get_attendance_claimed_today(self, obj):
        return attendance_state(obj)['claimed']


''', 'attendance_claimed_today = serializers.SerializerMethodField()')

patch('accounts/views.py', "from .models import User\n", "from .attendance import claim_attendance\nfrom .models import User\n", 'claim_attendance')
patch('accounts/views.py',
      "    def get(self, request):\n        return Response(UserSerializer(request.user).data)\n\n    def patch",
      "    def get(self, request):\n        from garden.sim import refill_water\n        refill_water(request.user)  # 시간이 지나 모인 물방울 반영\n"
      "        return Response(UserSerializer(request.user).data)\n\n    def patch",
      'refill_water(request.user)')
append_end('accounts/views.py', '''

class AttendanceView(APIView):
    """오늘 출석 보상 받기."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        result = claim_attendance(request.user)
        if result is None:
            return Response({'detail': '오늘은 이미 출석했어요.'}, status=400)
        extra = ' + 🎟️ 티켓 1장' if result['ticket'] else ''
        data = UserSerializer(request.user).data
        data.update({'detail': f"🎁 {result['day']}일차 출석! +{result['reward']}P{extra}", **result})
        return Response(data)
''', 'class AttendanceView')

patch('accounts/urls.py', 'from .views import AddPointsView, ConsumeTicketView, RegisterView, MeView',
      'from .views import AddPointsView, AttendanceView, ConsumeTicketView, RegisterView, MeView', 'AttendanceView, ConsumeTicketView')
insert_after('accounts/urls.py', r"^    path\('add-points/'.*\n",
             "    path('attendance/', AttendanceView.as_view(), name='attendance'),\n", "name='attendance'")

# =====================================================================
# garden
# =====================================================================
# --- sim.py: 균형 조정 + 물방울/햇빛 조각 ---
replace_line('garden/sim.py', r'^WATER_DECAY = .*$',
             'WATER_DECAY = 1.2          # 매 스텝 줄어드는 수분 (물방울이 한정 자원이라, 하루 한두 번 돌봐도 되게 느리게 했어요)',
             'WATER_DECAY = 1.2')
replace_line('garden/sim.py', r'^WATER_AMOUNT = .*$',
             'WATER_AMOUNT = 50          # 물방울 1개로 채워지는 수분', 'WATER_AMOUNT = 50')
insert_after('garden/sim.py', r'^MICROBE_AMOUNT = .*\n', '''
# ---- 물방울 · 햇빛 조각 (한정 자원) ----
WATER_CAP = 10             # 시간이 지나 저절로 모이는 물방울의 최대 보유량 (상점/미션으로 얻은 건 이보다 많아도 돼요)
WATER_REFILL_MINUTES = 30  # 물방울이 1개씩 모이는 간격 (빗물 모으기)
SUN_BOOST_AMOUNT = 50      # 햇빛 조각 1개가 더해주는 햇빛
SUN_BOOST_DECAY = 2.5      # 매 스텝 줄어드는 '더해준 햇빛'
PHOTO_PLANT_DAILY = 3      # 사진으로 식물 심기 하루 횟수
''', 'WATER_CAP = 10')
patch('garden/sim.py', "    sun = sun_levels(plots)\n    poll", "    ambient = sun_levels(plots)\n    poll", '    ambient = sun_levels(plots)')
patch('garden/sim.py', "        s = sun[p.slot_index]\n",
      "        p.sun_boost = max(0.0, p.sun_boost - SUN_BOOST_DECAY)\n"
      "        s = min(100.0, ambient[p.slot_index] + p.sun_boost)   # 실제로 받는 햇빛 = 그늘 반영한 기본 + 햇빛 조각\n",
      'p.sun_boost = max(0.0, p.sun_boost - SUN_BOOST_DECAY)')
patch('garden/sim.py', "PLOT_FIELDS = ['water', 'nutrients', 'microbes',", "PLOT_FIELDS = ['water', 'nutrients', 'microbes', 'sun_boost',",
      "'microbes', 'sun_boost',")
patch('garden/sim.py', "    ensure_plots(user)\n    now = timezone.now()", "    ensure_plots(user)\n    refill_water(user)\n    now = timezone.now()",
      '    refill_water(user)\n')
append_end('garden/sim.py', '''

def water_next_seconds(user, now=None):
    """다음 물방울이 모일 때까지 남은 초. 가득 찼으면 None."""
    if user.water_drops >= WATER_CAP:
        return None
    now = now or timezone.now()
    interval = WATER_REFILL_MINUTES * 60
    if user.water_refill_at is None:
        return interval
    return max(0, int(interval - (now - user.water_refill_at).total_seconds()))


def refill_water(user, now=None):
    """시간이 지난 만큼 물방울을 채워 저장해요 (30분에 1개, 최대 WATER_CAP개까지)."""
    now = now or timezone.now()
    if user.water_drops >= WATER_CAP:
        if user.water_refill_at is not None:
            user.water_refill_at = None
            user.save(update_fields=['water_refill_at'])
        return
    if user.water_refill_at is None:
        user.water_refill_at = now
        user.save(update_fields=['water_refill_at'])
        return
    interval = timedelta(minutes=WATER_REFILL_MINUTES)
    n = int((now - user.water_refill_at) // interval)
    if n <= 0:
        return
    user.water_drops = min(WATER_CAP, user.water_drops + n)
    user.water_refill_at = None if user.water_drops >= WATER_CAP else user.water_refill_at + interval * n
    user.save(update_fields=['water_drops', 'water_refill_at'])


def photo_plants_left(user):
    """오늘 사진으로 식물을 더 심을 수 있는 횟수."""
    if user.photo_plant_date != timezone.localdate():
        return PHOTO_PLANT_DAILY
    return max(0, PHOTO_PLANT_DAILY - user.photo_plant_count)
''', 'def refill_water')

# --- models.py ---
insert_after('garden/models.py', r'^    microbes = models\.FloatField\(default=10\).*\n',
             "    sun_boost = models.FloatField(default=0)    # 햇빛 조각으로 더해준 햇빛 0~100 (시간이 지나면 줄어요)\n",
             'sun_boost = models.FloatField')
patch('garden/models.py', "        self.death_reason = ''\n        self.photo = None",
      "        self.death_reason = ''\n        self.sun_boost = 0\n        self.photo = None", 'self.sun_boost = 0')

# --- serializers.py ---
patch('garden/serializers.py', "    sun = serializers.SerializerMethodField()\n",
      "    sun = serializers.SerializerMethodField()\n    sun_ambient = serializers.SerializerMethodField()\n    sun_boost = serializers.SerializerMethodField()\n",
      'sun_ambient = serializers.SerializerMethodField()')
patch('garden/serializers.py', "'water', 'nutrients', 'microbes', 'sun', 'growth_speed', 'photo', 'pixel_photo',",
      "'water', 'nutrients', 'microbes', 'sun', 'sun_ambient', 'sun_boost', 'growth_speed', 'photo', 'pixel_photo',",
      "'sun', 'sun_ambient', 'sun_boost'")
patch('garden/serializers.py',
      "    def _sun(self, obj):\n        return self.context.get('sun', {}).get(obj.slot_index, 100.0)\n",
      "    def _ambient(self, obj):\n        return self.context.get('sun', {}).get(obj.slot_index, 100.0)\n\n"
      "    def _sun(self, obj):\n        return min(100.0, self._ambient(obj) + obj.sun_boost)   # 실제로 받는 햇빛\n",
      'def _ambient(self, obj):')
patch('garden/serializers.py', "    def get_sun(self, obj): return round(self._sun(obj))\n",
      "    def get_sun(self, obj): return round(self._sun(obj))\n"
      "    def get_sun_ambient(self, obj): return round(self._ambient(obj))\n"
      "    def get_sun_boost(self, obj): return round(obj.sun_boost)\n",
      'def get_sun_ambient')

# --- views.py ---
patch('garden/views.py', "from rest_framework import generics, permissions, status",
      "from io import BytesIO\n\nfrom django.utils import timezone\nfrom PIL import Image, ImageOps\nfrom rest_framework import generics, permissions, status",
      'from PIL import Image, ImageOps')
patch('garden/views.py', "from . import sim\n", "from . import sim\nfrom .ai import AIUnavailable, identify_plant\n", 'from .ai import')
patch('garden/views.py', "        'microbes': user.microbes,\n        'diversity'",
      "        'microbes': user.microbes,\n"
      "        'water_drops': user.water_drops,                 # 보유 물방울\n"
      "        'sunlight': user.sunlight,                       # 보유 햇빛 조각\n"
      "        'water_cap': sim.WATER_CAP,\n"
      "        'water_next_seconds': sim.water_next_seconds(user),   # 다음 물방울까지 남은 시간(초), 가득이면 null\n"
      "        'photo_plants_left': sim.photo_plants_left(user),     # 오늘 사진으로 더 심을 수 있는 횟수\n"
      "        'diversity'",
      "'water_drops': user.water_drops,")
replace_range('garden/views.py', 'class WaterPlotView(APIView):', 'class FeedPlotView(APIView):', '''class WaterPlotView(APIView):
    """물 주기: 물방울 1개를 써서 흙의 수분을 채워요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        plot, err = _living_plot(request.user, slot_index)
        if err:
            return err
        user = request.user
        if user.water_drops < 1:
            return _bad('물방울이 없어요. 30분마다 1개씩 모이고, 미션이나 상점에서도 얻을 수 있어요.')
        if plot.water >= 100:
            return _bad('물이 이미 가득해요.')
        user.water_drops -= 1
        user.save(update_fields=['water_drops'])
        plot.water = min(100.0, plot.water + sim.WATER_AMOUNT)
        plot.save(update_fields=['water'])
        return Response(garden_state(user, '💧 물을 줬어요'))


class SunlightPlotView(APIView):
    """햇빛 주기: 햇빛 조각 1개를 써서 그늘 때문에 모자란 햇빛을 채워요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        plot, err = _living_plot(request.user, slot_index)
        if err:
            return err
        user = request.user
        if user.sunlight < 1:
            return _bad('햇빛 조각이 없어요. 사진 미션을 하거나 상점에서 구할 수 있어요.')
        ambient = sim.sun_levels(list(GardenPlot.objects.filter(user=user).select_related('seed_type')))[plot.slot_index]
        if min(100.0, ambient + plot.sun_boost) >= 100:
            return _bad('햇빛이 이미 충분해요. 그늘진 칸에 써 보세요.')
        user.sunlight -= 1
        user.save(update_fields=['sunlight'])
        plot.sun_boost = min(100.0, plot.sun_boost + sim.SUN_BOOST_AMOUNT)
        plot.save(update_fields=['sun_boost'])
        return Response(garden_state(user, '☀️ 햇빛을 채웠어요'))


''', 'class SunlightPlotView')
replace_range('garden/views.py', 'class PlantPhotoView(APIView):', None, '''def _prepare_image(upload):
    """업로드된 사진을 안전하게 줄여서 JPEG 바이트로 돌려줘요. (위치 정보 같은 EXIF는 이 과정에서 사라져요)"""
    if upload.size > 12 * 1024 * 1024:
        raise ValueError('사진이 너무 커요.')
    img = ImageOps.exif_transpose(Image.open(upload)).convert('RGB')
    img.thumbnail((1024, 1024))
    buf = BytesIO()
    img.save(buf, 'JPEG', quality=85)
    return buf.getvalue()


class PlantPhotoView(APIView):
    """
    사진 속 식물을 AI가 알아봐서, 그 종을 정원의 빈 화분에 진짜 식물(새싹)로 심어요.
    상점에서 산 식물과 똑같이 물·햇빛·영양분을 주며 키울 수 있어요.
    사진은 서버에 저장하지 않아요 (AI가 보고 바로 버려요).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        upload = request.data.get('photo')
        if upload is None:
            return _bad('사진이 필요해요.')

        user = request.user
        sim.advance(user)
        plot = GardenPlot.objects.filter(user=user, slot_index=slot_index).first()
        if plot is None or not plot.is_empty:
            return _bad('빈 화분이 아니에요.')
        if sim.photo_plants_left(user) < 1:
            return _bad(f'오늘은 사진으로 심을 수 있는 횟수({sim.PHOTO_PLANT_DAILY}번)를 다 썼어요. 내일 다시 해봐요!')

        try:
            image = _prepare_image(upload)
        except Exception:
            return _bad('사진 파일을 읽을 수 없어요. 다른 사진으로 해볼까요?')

        try:
            found = identify_plant(image)
        except AIUnavailable:
            return Response({'detail': 'AI를 아직 쓸 수 없어요. (서버에 GEMINI_API_KEY 설정이 필요해요)'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            return Response({'detail': 'AI가 잠시 바빠요. 조금 뒤에 다시 시도해 주세요.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        species = SeedType.objects.filter(key=found['species_key']).first() if found['species_key'] else None
        if not found['is_plant'] or species is None:
            return _bad('어떤 식물인지 알아보지 못했어요. 나무나 꽃이 잘 보이게 가까이에서 다시 찍어볼까요?')

        plot.seed_type = species
        plot.growth_stage = 1                 # 새싹으로 시작해요
        plot.growth_progress = 0
        plot.stress = 0
        plot.stress_reason = ''
        plot.death_reason = ''
        plot.save()

        today = timezone.localdate()
        if user.photo_plant_date != today:
            user.photo_plant_date, user.photo_plant_count = today, 0
        user.photo_plant_count += 1
        user.save(update_fields=['photo_plant_date', 'photo_plant_count'])

        similar = '' if found['match'] == 'exact' else ' (목록에서 가장 비슷한 종으로 심었어요)'
        data = garden_state(user, f"🔍 AI가 {species.name}(으)로 알아봤어요!{similar}")
        data['identified'] = {
            'key': species.key, 'name': species.name, 'emoji': species.emoji, 'kind': species.kind,
            'match': found['match'], 'label': found['label'], 'reason': found['reason'],
        }
        return Response(data)
''', 'def _prepare_image')

# --- urls.py ---
patch('garden/urls.py', 'PlantSeedView, SeedInventoryView, SpeciesListView, WaterPlotView)',
      'PlantSeedView, SeedInventoryView, SpeciesListView, SunlightPlotView, WaterPlotView)', 'SpeciesListView, SunlightPlotView, WaterPlotView)')
patch('garden/urls.py', "    path('<int:slot_index>/feed/',",
      "    path('<int:slot_index>/sunlight/', SunlightPlotView.as_view(), name='plot-sunlight'),\n    path('<int:slot_index>/feed/',",
      "name='plot-sunlight'")

# =====================================================================
# missions
# =====================================================================
insert_after('missions/models.py', r'^    reward_tickets = models\.PositiveIntegerField\(default=1\).*\n',
             "    reward_water = models.PositiveIntegerField(default=1)      # 보상으로 주는 물방울\n"
             "    reward_sunlight = models.PositiveIntegerField(default=0)   # 보상으로 주는 햇빛 조각 (사진 미션: 밖에 나가 햇빛을 쬔 보상!)\n",
             'reward_water = models.PositiveIntegerField')
patch('missions/serializers.py', "'reward_points', 'reward_tickets', 'requires_photo',",
      "'reward_points', 'reward_tickets', 'reward_water', 'reward_sunlight', 'requires_photo',", "'reward_water', 'reward_sunlight'")
patch('missions/views.py',
      "    user.points += mission.reward_points\n    user.tickets += mission.reward_tickets\n    user.save(update_fields=['points', 'tickets'])",
      "    user.points += mission.reward_points\n    user.tickets += mission.reward_tickets\n    user.water_drops += mission.reward_water\n"
      "    user.sunlight += mission.reward_sunlight\n    user.save(update_fields=['points', 'tickets', 'water_drops', 'sunlight'])\n\n\n"
      "def reward_text(mission):\n    parts = [f'+{mission.reward_points}P', f'티켓 +{mission.reward_tickets}']\n"
      "    if mission.reward_water:\n        parts.append(f'💧+{mission.reward_water}')\n"
      "    if mission.reward_sunlight:\n        parts.append(f'☀️+{mission.reward_sunlight}')\n    return ', '.join(parts)",
      'def reward_text(mission)')
patch('missions/views.py',
      "            'detail': f'미션 완료!{label_part} +{mission.reward_points}P, 티켓 +{mission.reward_tickets}',\n"
      "            'points': request.user.points,\n            'tickets': request.user.tickets,",
      "            'detail': f'미션 완료!{label_part} {reward_text(mission)}',\n"
      "            'points': request.user.points,\n            'tickets': request.user.tickets,\n"
      "            'water_drops': request.user.water_drops,\n            'sunlight': request.user.sunlight,",
      "'detail': f'미션 완료!{label_part} {reward_text(mission)}'")
patch('missions/views.py',
      "                'detail': f'퀴즈 성공! {correct}/{total} · +{mission.reward_points}P, 티켓 +{mission.reward_tickets}',\n"
      "                'points': request.user.points, 'tickets': request.user.tickets,",
      "                'detail': f'퀴즈 성공! {correct}/{total} · {reward_text(mission)}',\n"
      "                'points': request.user.points, 'tickets': request.user.tickets,\n"
      "                'water_drops': request.user.water_drops, 'sunlight': request.user.sunlight,",
      "퀴즈 성공! {correct}/{total} · {reward_text(mission)}")

SEED = 'missions/management/commands/seed_demo_data.py'
patch(SEED, "            mission, _ = Mission.objects.get_or_create(\n                title=title,",
      "            mission, created = Mission.objects.get_or_create(\n                title=title,", 'mission, created = Mission.objects.get_or_create(')
patch(SEED, "            if mission.mission_type != mtype:",
      "            # 보상 물방울/햇빛 조각: 사진 미션은 💧1 + ☀️1, 퀴즈는 💧2.\n"
      "            # (관리자가 따로 바꾼 미션은 건드리지 않아요)\n"
      "            want = (1, 1) if mtype == 'photo' else (2, 0)\n"
      "            if created or (mission.reward_water, mission.reward_sunlight) == (1, 0):\n"
      "                mission.reward_water, mission.reward_sunlight = want\n"
      "                mission.save(update_fields=['reward_water', 'reward_sunlight'])\n"
      "            if mission.mission_type != mtype:",
      "want = (1, 1) if mtype == 'photo' else (2, 0)")
patch(SEED, "        ShopItem.objects.get_or_create(\n            item_type='ticket',",
      "        ShopItem.objects.get_or_create(\n            item_type='water', name='물방울 5개', emoji='💧',\n"
      "            defaults=dict(description='나무에 물을 줄 수 있어요 (30분마다 1개씩 저절로도 모여요)', price=10, quantity=5),\n        )\n"
      "        ShopItem.objects.get_or_create(\n            item_type='sunlight', name='햇빛 조각', emoji='☀️',\n"
      "            defaults=dict(description='그늘진 칸에 햇빛을 채워줘요', price=15, quantity=1),\n        )\n"
      "        ShopItem.objects.get_or_create(\n            item_type='ticket',",
      "item_type='water', name='물방울 5개'")
patch('missions/management/commands/generate_missions.py', "            'requires_photo': mtype == 'photo',",
      "            'reward_water': 1 if mtype == 'photo' else 2,\n            'reward_sunlight': 1 if mtype == 'photo' else 0,\n            'requires_photo': mtype == 'photo',",
      "'reward_water': 1 if mtype == 'photo' else 2,")

# =====================================================================
# shop
# =====================================================================
insert_after('shop/models.py', r"^\s+\('microbe', '미생물제'\),.*\n",
             "        ('water', '물방울'),\n        ('sunlight', '햇빛 조각'),\n", "('water', '물방울')")
insert_after('shop/models.py', r'^    price = models\.PositiveIntegerField\(\)\n',
             "    quantity = models.PositiveIntegerField(default=1)  # 한 번 사면 몇 개를 받는지 (예: 물방울 5개 묶음)\n",
             'quantity = models.PositiveIntegerField')
patch('shop/serializers.py', "fields = ('id', 'item_type', 'name', 'emoji', 'description', 'price', 'seed_key')",
      "fields = ('id', 'item_type', 'name', 'emoji', 'description', 'price', 'quantity', 'seed_key')", "'price', 'quantity', 'seed_key'")
patch('shop/views.py', "        elif item.item_type == 'microbe':\n            user.microbes += 1\n",
      "        elif item.item_type == 'microbe':\n            user.microbes += 1\n"
      "        elif item.item_type == 'water':\n            user.water_drops += item.quantity\n"
      "        elif item.item_type == 'sunlight':\n            user.sunlight += item.quantity\n",
      "item.item_type == 'water'")
patch('shop/views.py', "            'microbes': user.microbes,\n        })",
      "            'microbes': user.microbes,\n            'water_drops': user.water_drops,\n            'sunlight': user.sunlight,\n        })",
      "'water_drops': user.water_drops,")

# =====================================================================
print('\n=== 결과 ===')
if FAIL:
    print('⚠️  맞지 않는 부분이 있어서 **아무 파일도 고치지 않았어요** (반쯤 고쳐진 상태가 되지 않게 했어요):')
    for line in FAIL:
        print('  ✗ ' + line)
    print('\n→ 이 메시지를 그대로 알려주시거나, 프로젝트 폴더를 zip으로 올려주세요. 맞춰서 다시 만들어 드릴게요.')
    sys.exit(1)
flush()
for line in DONE:
    print('  ' + line)
print(f'''
✅ 모두 적용됐어요. 원본은 {BACKUP}/ 에 백업했어요.
이제 터미널에서 한 줄씩 실행하세요:
    python manage.py makemigrations
    python manage.py migrate
    python manage.py seed_demo_data
그리고 AI 사진 심기를 쓰려면 서버를 켜는 터미널에서 GEMINI_API_KEY를 설정해 주세요.''')
