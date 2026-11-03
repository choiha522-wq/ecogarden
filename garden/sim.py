"""
정원 생태 시뮬레이션.

현실의 시간이 흐르면 게임 속 정원도 변해요. 서버는 "마지막으로 계산한 뒤 시간이 얼마나 지났는지"를 보고
그만큼의 단계(스텝)를 한꺼번에 계산합니다 (접속해 있지 않아도 정원은 계속 변해요).

한 스텝 = 현실 GARDEN_STEP_MINUTES분 (기본 10분).

[규칙 요약]
- 공기 중 CO2: 매 스텝 조금씩 늘고, 자란 나무가 흡수해서 줄어요. 죽은 나무를 방치하면 다시 내뿜어요.
- 나무: 물·영양분·햇빛이 있어야 하고, CO2가 너무 높아도 힘들어해요. 힘든 상태가 이어지면 죽어요.
- 성장: 물, 햇빛, 미생물이 많을수록 빨리 자라요.
- 햇빛: 주변에 다 자란 큰 나무가 많을수록 그늘이 져서 줄어요. (꽃은 그늘을 만들지 않아요)
- 종마다 필요한 물·햇빛·흙이 달라요 (species_data.py). 꽃은 탄소를 조금만 흡수하지만 빨리 자라고,
  꽃이 활짝 피면 벌·나비가 찾아와 정원 전체의 성장이 빨라져요 (꽃가루받이 보너스).
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import KOREA_AVG_CO2_PPM

from .models import GardenPlot, GardenProgress
from .progression import grid_size_for_level, unlocked_slot_indexes, record_completed_plants

# ================= 난이도 조절용 숫자 (여기만 고치면 돼요) =================
CO2_BASELINE = KOREA_AVG_CO2_PPM   # 시작 농도: 한국 평균
CO2_LIMIT = 500.0          # 이 농도를 넘으면 나무가 힘들어해요 (기상청 전망: 지금 속도면 2050년경 약 499ppm)
CO2_MIN, CO2_MAX = 350.0, 600.0
EMISSION_PER_STEP = 0.6    # 아무것도 안 해도 매 스텝 늘어나는 양(ppm)
ABSORB_PER_STAGE = 0.12    # 나무 1그루가 매 스텝 (성장단계 × 이 값)만큼 흡수
DEAD_RELEASE = 0.25        # 죽은 나무 1그루가 방치되면 매 스텝 내뿜는 양

WATER_DECAY = 1.2          # 매 스텝 줄어드는 수분 (물방울이 한정 자원이라, 하루 한두 번 돌봐도 되게 느리게 했어요)
NUTRIENT_USE = 1.2         # 나무가 매 스텝 쓰는 영양분
NUTRIENT_FROM_MICROBES = 1.0   # 미생물 100%일 때 매 스텝 분해로 생기는 영양분
MICROBE_DECAY = 0.3        # 매 스텝 줄어드는 미생물

SHADE_PER_BIG_NEIGHBOR = 12.0  # 주변의 다 자란(3단계 이상) 나무 1그루당 줄어드는 햇빛 (이웃 6그루 이상이면 햇빛 부족)
# (햇빛이 모자란 기준은 종마다 달라요: 6 × 햇빛 필요도. 필요도 5면 30 밑에서 힘들어해요)

STRESS_LIMIT = 6           # 이만큼 연속으로 힘들면 죽어요
GROWTH_BASE = 0.1          # 좋은 조건에서 매 스텝 성장 진행도 (1이 되면 한 단계 성장)
MAX_CATCHUP_STEPS = 72     # 한 번에 따라잡는 최대 스텝 (오래 자리를 비워도 정원이 한꺼번에 망가지지 않게)

WATER_AMOUNT = 50          # 물방울 1개로 채워지는 수분
FEED_AMOUNT = 40           # 영양제 1개
MICROBE_AMOUNT = 40        # 미생물제 1개

# ---- 물방울 · 햇빛 조각 (한정 자원) ----
WATER_CAP = 10             # 시간이 지나 저절로 모이는 물방울의 최대 보유량 (상점/미션으로 얻은 건 이보다 많아도 돼요)
WATER_REFILL_MINUTES = 30  # 물방울이 1개씩 모이는 간격 (빗물 모으기)
SUN_BOOST_AMOUNT = 50      # 햇빛 조각 1개가 더해주는 햇빛
SUN_BOOST_DECAY = 2.5      # 매 스텝 줄어드는 '더해준 햇빛'
PHOTO_PLANT_DAILY = 3      # 사진으로 식물 심기 하루 횟수

# 종별 특성 (species_data.py의 water/sun/soil 값 3이 '보통'이에요)
FLOWER_ABSORB_PER_STAGE = 0.03   # 꽃은 나무보다 탄소를 훨씬 적게 흡수해요
FLOWER_GROWTH = 1.5              # 꽃은 나무보다 빨리 자라요
POLLINATION_PER_SPECIES = 0.08   # 활짝 핀 꽃 '종류' 1개당 정원 전체 성장 보너스 (같은 꽃을 여러 개 심어도 1번만 세요)
POLLINATION_CAP = 0.32           # 보너스 최대치 (+32%)

MAX_PLOT_COUNT = 25
GRID_STRIDE = 5
# ===========================================================================


def step_minutes():
    return getattr(settings, 'GARDEN_STEP_MINUTES', 10)


def ensure_plots(user):
    """사용자의 정원 칸을 최대 크기까지 준비해요. 레벨에 따라 일부만 열려요."""
    existing = set(GardenPlot.objects.filter(user=user).values_list('slot_index', flat=True))
    missing = [i for i in range(MAX_PLOT_COUNT) if i not in existing]
    if missing:
        GardenPlot.objects.bulk_create([GardenPlot(user=user, slot_index=i) for i in missing])


def _is_living_tree(p):
    """그늘을 만들 수 있는 '살아있는 나무' (꽃은 제외)."""
    return bool(p.seed_type_id) and not p.is_dead and p.seed_type.kind == 'tree'


def _is_living_plant(p):
    return bool(p.seed_type_id) and not p.is_dead


def pollination_bonus(plots):
    """활짝 핀(개화) 꽃의 종류가 많을수록 정원 전체의 성장이 빨라져요. 1.0 = 보너스 없음."""
    kinds = {p.seed_type_id for p in plots
             if _is_living_plant(p) and p.seed_type.kind == 'flower' and p.growth_stage >= 4}
    return 1.0 + min(POLLINATION_CAP, POLLINATION_PER_SPECIES * len(kinds))


def diversity(plots):
    """살아있는 식물의 종류 수."""
    return len({p.seed_type_id for p in plots if _is_living_plant(p)})


def sun_levels(plots, size=3):
    """칸마다 햇빛(0~100). 이웃한 8칸에 다 자란 나무가 많을수록 그늘이 져요."""
    by_slot = {p.slot_index: p for p in plots}
    out = {}
    for i in unlocked_slot_indexes(size):
        r, c = divmod(i, GRID_STRIDE)
        big = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < size and 0 <= cc < size:
                    n = by_slot.get(rr * GRID_STRIDE + cc)
                    if n and _is_living_tree(n) and n.growth_stage >= 3:
                        big += 1
        out[i] = max(0.0, 100.0 - SHADE_PER_BIG_NEIGHBOR * big)
    return out


def growth_speed(plot, sun, pollination=1.0):
    """현재 조건에서의 성장 속도 배율 (1.0 = 기본). 화면에 '성장 속도 ×N'으로 보여줘요."""
    base = (0.6 + 0.4 * plot.water / 100) * (0.6 + 0.4 * sun / 100) * (1 + 0.8 * plot.microbes / 100)
    kind_mult = FLOWER_GROWTH if plot.seed_type and plot.seed_type.kind == 'flower' else 1.0
    return round(base * kind_mult * pollination, 2)


def _step(plots, co2, size):
    ambient = sun_levels(plots, size)
    poll = pollination_bonus(plots)
    absorbed = released = 0.0

    for p in plots:
        if not p.seed_type_id:
            continue  # 빈 칸, 사진 식물은 시뮬레이션하지 않아요
        st = p.seed_type
        is_flower = st.kind == 'flower'
        if p.is_dead:
            released += DEAD_RELEASE * (0.5 if is_flower else 1.0)
            continue

        # 종마다 필요한 양이 달라요 (필요도 3 = 기본). 물을 좋아하는 종은 물이 빨리 마르고,
        # 햇빛을 좋아하는 종은 그늘에 약하고, 기름진 흙이 필요한 종은 영양분을 많이 써요.
        water_decay = WATER_DECAY * (0.4 + 0.2 * st.water_need)
        nutrient_use = NUTRIENT_USE * (0.4 + 0.2 * st.soil_need)
        sun_min = 6.0 * st.sun_need

        # 1) 흙 상태 변화
        p.water = max(0.0, p.water - water_decay)
        p.microbes = max(0.0, p.microbes - MICROBE_DECAY)
        p.nutrients = min(100.0, max(0.0, p.nutrients - nutrient_use + NUTRIENT_FROM_MICROBES * p.microbes / 100))
        p.sun_boost = max(0.0, p.sun_boost - SUN_BOOST_DECAY)
        s = min(100.0, ambient[p.slot_index] + p.sun_boost)   # 실제로 받는 햇빛 = 그늘 반영한 기본 + 햇빛 조각

        # 2) 힘든 이유 판정 (우선순위: 물 > 영양분 > 햇빛 > 탄소)
        reason = ''
        if p.water <= 0:
            reason = 'water'
        elif p.nutrients <= 0:
            reason = 'nutrients'
        elif s < sun_min:
            reason = 'sun'
        elif co2 > CO2_LIMIT:
            reason = 'co2'

        if reason:
            p.stress += 1
            p.stress_reason = reason
            if p.stress >= STRESS_LIMIT:
                p.death_reason = reason
        else:
            p.stress = max(0, p.stress - 1)
            if p.stress == 0:
                p.stress_reason = ''
            # 3) 성장: 물·햇빛·미생물이 많을수록 빨라요
            if p.growth_stage < 4:
                p.growth_progress += GROWTH_BASE * growth_speed(p, s, poll)
                while p.growth_progress >= 1 and p.growth_stage < 4:
                    p.growth_progress -= 1
                    p.growth_stage += 1
            if p.growth_stage >= 4:
                p.growth_progress = 0

        # 4) 탄소 흡수 (살아있고 싹이 튼 나무만)
        if not p.is_dead and p.growth_stage >= 1:
            absorbed += (FLOWER_ABSORB_PER_STAGE if is_flower else ABSORB_PER_STAGE) * p.growth_stage

    co2 = co2 + EMISSION_PER_STEP - absorbed + released
    return max(CO2_MIN, min(CO2_MAX, co2))


PLOT_FIELDS = ['water', 'nutrients', 'microbes', 'sun_boost', 'growth_stage', 'growth_progress',
               'stress', 'stress_reason', 'death_reason']


def run_steps(user, steps):
    plots = list(GardenPlot.objects.filter(user=user).select_related('seed_type'))
    progress, _ = GardenProgress.objects.get_or_create(user=user)
    size = grid_size_for_level(progress.level)
    co2 = user.co2_ppm
    for _ in range(steps):
        co2 = _step(plots, co2, size)
    with transaction.atomic():
        GardenPlot.objects.bulk_update(plots, PLOT_FIELDS)
    user.co2_ppm = co2


def advance(user, steps=None):
    """
    마지막 계산 이후 지난 시간만큼 정원을 계산해서 저장.
    steps를 직접 주면(시연용) 시간과 상관없이 그만큼 계산해요.
    """
    ensure_plots(user)
    refill_water(user)
    now = timezone.now()

    if steps is not None:
        run_steps(user, steps)
        user.save(update_fields=['co2_ppm'])
        return steps

    if user.garden_updated_at is None:
        user.garden_updated_at = now
        user.save(update_fields=['garden_updated_at'])
        return 0

    minutes = (now - user.garden_updated_at).total_seconds() / 60
    n = int(minutes // step_minutes())
    if n <= 0:
        return 0

    if n > MAX_CATCHUP_STEPS:
        n = MAX_CATCHUP_STEPS
        user.garden_updated_at = now  # 오래 비웠으면 나머지 시간은 건너뜀
    else:
        user.garden_updated_at = user.garden_updated_at + timedelta(minutes=step_minutes() * n)

    run_steps(user, n)
    user.save(update_fields=['co2_ppm', 'garden_updated_at'])
    return n


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
