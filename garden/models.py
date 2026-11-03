from django.conf import settings
from django.db import models

GROWTH_STAGES = ['씨앗', '새싹', '줄기', '묘목', '나무']
FLOWER_STAGES = ['씨앗', '새싹', '줄기', '봉오리', '개화']


class SeedType(models.Model):
    """
    씨앗 종류(나무/꽃). 종마다 필요한 물·햇빛·흙이 달라서 시뮬레이션(garden/sim.py)에 반영돼요.
    실제 데이터는 garden/species_data.py에 있고, seed_demo_data 커맨드가 DB에 넣어줘요.
    """
    KIND_CHOICES = [('tree', '나무'), ('flower', '꽃')]
    DIFFICULTY_CHOICES = [(1, '쉬움'), (2, '보통'), (3, '어려움')]
    SHAPE_CHOICES = [('round', '활엽수'), ('conifer', '침엽수'), ('tall', '키 큰 나무'), ('willow', '늘어지는 나무')]
    ORIGIN_CHOICES = [('native', '자생'), ('introduced', '외래'), ('cultivated', '재배종/원예종'), ('unverified', '확인 중')]

    key = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=8)
    description = models.CharField(max_length=200, blank=True)
    price = models.PositiveIntegerField(default=30)

    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='tree')
    difficulty = models.PositiveSmallIntegerField(default=1, choices=DIFFICULTY_CHOICES, help_text='쉬움·보통·어려움 3단계')
    unlock_level = models.PositiveSmallIntegerField(default=1, help_text='이 정원 레벨에서 도감과 상점이 열려요.')
    season = models.CharField(max_length=10, blank=True)                # 꽃 피는 계절 (표시용)
    water_need = models.PositiveSmallIntegerField(default=3)            # 물이 필요한 정도 1~5
    sun_need = models.PositiveSmallIntegerField(default=3)              # 햇빛이 필요한 정도 1~5
    soil_need = models.PositiveSmallIntegerField(default=3)             # 기름진 흙이 필요한 정도 1~5
    benefits = models.CharField(max_length=100, blank=True)             # 생태계에 주는 도움 (쉼표로 구분)
    scientific_name = models.CharField(max_length=100, blank=True)
    origin_status = models.CharField(max_length=12, choices=ORIGIN_CHOICES, default='unverified')
    ecology_notes = models.CharField(max_length=240, blank=True)
    source_title = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    reference_image_url = models.URLField(max_length=500, blank=True)

    # --- 3D 정원에서 보이는 모양 ---
    shape = models.CharField(max_length=10, choices=SHAPE_CHOICES, default='round')
    palette = models.CharField(max_length=30, default='2E9E52,3FB765,5CD07A')  # 잎 색 3가지 (RRGGBB)
    accent = models.CharField(max_length=6, blank=True)                  # 꽃/열매 색
    trunk = models.CharField(max_length=6, default='8B5A2B')             # 줄기 색
    width = models.FloatField(default=1.0)                               # 나무 폭 배율
    stem_height = models.FloatField(default=1.0)                         # 꽃 줄기 높이
    stem_count = models.PositiveSmallIntegerField(default=3)             # 꽃 포기 수
    center = models.CharField(max_length=6, default='FFC107')            # 꽃 가운데 색

    def __str__(self):
        return self.name


class GardenProgress(models.Model):
    """레벨별 요구 난이도 식물을 끝까지 키운 누적 기록."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='garden_progress')
    theme = models.CharField(max_length=12, default='spring')
    owned_themes = models.JSONField(default=list, blank=True)
    level = models.PositiveIntegerField(default=1)
    easy_completed = models.PositiveIntegerField(default=0)
    medium_completed = models.PositiveIntegerField(default=0)
    hard_completed = models.PositiveIntegerField(default=0)

    @property
    def total_completed(self):
        return self.easy_completed + self.medium_completed + self.hard_completed


class UserSeedInventory(models.Model):
    """사용자가 보유한 씨앗 수량. 상점에서 구매하면 여기 quantity가 늘어남."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seed_inventory')
    seed_type = models.ForeignKey(SeedType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'seed_type')


class GardenPlot(models.Model):
    """
    사용자 정원의 한 칸. 슬롯은 최대 5x5이며 레벨별로 일부만 열려요.
    seed_type이 null이면 빈 화분. photo가 있으면 사용자가 직접 찍은 사진을 심은 상태
    (index.html의 ty=='photo' 케이스 — 픽셀화는 save() 시 자동 처리).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='garden_plots')
    slot_index = models.PositiveSmallIntegerField()
    seed_type = models.ForeignKey(SeedType, on_delete=models.SET_NULL, null=True, blank=True)
    growth_stage = models.PositiveSmallIntegerField(default=0)  # 0=씨앗 ~ 4=나무
    photo = models.ImageField(upload_to='garden_photos/', blank=True, null=True)
    pixel_photo = models.ImageField(upload_to='garden_photos/pixel/', blank=True, null=True)

    # --- 생태 시뮬레이션 (garden/sim.py가 시간에 따라 갱신) ---
    water = models.FloatField(default=70)       # 흙 수분 0~100
    nutrients = models.FloatField(default=70)   # 흙 영양분 0~100
    microbes = models.FloatField(default=10)    # 흙 속 미생물 0~100
    sun_boost = models.FloatField(default=0)    # 햇빛 조각으로 더해준 햇빛 0~100 (시간이 지나면 줄어요)
    growth_progress = models.FloatField(default=0)  # 다음 성장 단계까지 진행도 0~1
    completion_recorded = models.BooleanField(default=False)  # 완전히 자란 식물은 한 번만 레벨 진행에 반영
    stress = models.PositiveSmallIntegerField(default=0)  # 연속으로 힘들었던 횟수
    stress_reason = models.CharField(max_length=20, blank=True)  # water / nutrients / sun / co2
    death_reason = models.CharField(max_length=20, blank=True)   # 비어있지 않으면 시든 나무

    class Meta:
        unique_together = ('user', 'slot_index')
        ordering = ['slot_index']

    def __str__(self):
        return f'{self.user} #{self.slot_index}'

    @property
    def is_empty(self):
        return self.seed_type_id is None and not self.photo

    @property
    def is_dead(self):
        return bool(self.death_reason)

    def reset_plant(self):
        """화분을 비울 때: 식물 상태만 초기화하고 흙 상태는 그대로 둠."""
        self.seed_type = None
        self.growth_stage = 0
        self.growth_progress = 0
        self.completion_recorded = False
        self.stress = 0
        self.stress_reason = ''
        self.death_reason = ''
        self.sun_boost = 0
        self.photo = None
        self.pixel_photo = None

    @property
    def growth_stage_label(self):
        stages = FLOWER_STAGES if self.seed_type and self.seed_type.kind == 'flower' else GROWTH_STAGES
        return stages[self.growth_stage]

    def make_pixel_art(self, size=20):
        """
        업로드된 사진을 작은 격자로 리사이즈해 픽셀 아트 느낌으로 변환.
        index.html의 photo() 함수(캔버스로 20x20 축소 + 색상 양자화)를 서버 쪽으로 옮긴 버전.
        배경 제거(rembg)는 추후 단계에서 이 앞에 끼워 넣으면 됨 (TODO).
        """
        from io import BytesIO
        from django.core.files.base import ContentFile
        from PIL import Image

        if not self.photo:
            return

        img = Image.open(self.photo).convert('RGB')
        w, h = img.size
        m = min(w, h)
        img = img.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
        img = img.resize((size, size), Image.NEAREST)
        img = img.quantize(colors=32).convert('RGB')
        img = img.resize((size * 10, size * 10), Image.NEAREST)

        buf = BytesIO()
        img.save(buf, format='PNG')
        self.pixel_photo.save(f'plot_{self.pk}.png', ContentFile(buf.getvalue()), save=False)


class PlantCollection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    seed_type = models.ForeignKey(SeedType, on_delete=models.CASCADE)
    harvested_count = models.PositiveIntegerField(default=0)
    first_collected_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'seed_type'], name='unique_plant_collection')]


class WeeklyGoalClaim(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    week_start = models.DateField()
    claimed_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'week_start'], name='unique_weekly_goal_claim')]
