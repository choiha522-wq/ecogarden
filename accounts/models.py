from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from uuid import uuid4


# 한국 이산화탄소 배경농도(ppm) - 기상청 국립기상과학원 '2025 지구대기감시보고서' 기준
KOREA_AVG_CO2_PPM = 432.7


# 지역은 시·도까지만 선택하게 해요 (상세 주소는 받지 않아요)
REGION_CHOICES = [(x, x) for x in (
    '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기',
    '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
)]
SCHOOL_CHOICES = [('elementary', '초등학생'), ('middle', '중학생'), ('high', '고등학생')]


class User(AbstractUser):
    """
    기본 Django User에 서비스 전용 재화(포인트, 게임 티켓, 영양제)를 추가한 커스텀 유저 모델.
    index.html 프로토타입의 S.pt / S.tk / S.nutri 상태를 DB로 옮긴 것.
    """
    points = models.PositiveIntegerField(default=0)
    tickets = models.PositiveIntegerField(default=0)
    nutrients = models.PositiveIntegerField(default=0)
    microbes = models.PositiveIntegerField(default=0)  # 보유한 미생물제 개수
    water_drops = models.PositiveIntegerField(default=5)   # 보유한 물방울 (물 주기에 1개씩 써요)
    water_refill_at = models.DateTimeField(null=True, blank=True)  # 다음 물방울이 모이기 시작한 시각
    sunlight = models.PositiveIntegerField(default=1)      # 보유한 햇빛 조각 (햇빛 주기에 1개씩 써요)
    co2_ppm = models.FloatField(default=KOREA_AVG_CO2_PPM)  # 내 정원이 있는 공기 중 CO2 농도
    garden_updated_at = models.DateTimeField(null=True, blank=True)  # 정원 시뮬레이션을 마지막으로 계산한 시각

    # --- 출석 (서버에 저장해요) ---
    attendance_streak = models.PositiveSmallIntegerField(default=0)   # 이번 7일 주기에서 출석한 날 수
    attendance_date = models.DateField(null=True, blank=True)         # 마지막으로 출석한 날

    # --- 사진으로 식물 심기: 하루 횟수 제한 ---
    photo_plant_date = models.DateField(null=True, blank=True)
    photo_plant_count = models.PositiveSmallIntegerField(default=0)
    friend_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # --- 회원가입 정보 / 마이페이지 ---
    region_sido = models.CharField('시·도', max_length=10, choices=REGION_CHOICES, blank=True)
    region_sigungu = models.CharField('시·군·구', max_length=30, blank=True)
    school_level = models.CharField('학교급', max_length=12, choices=SCHOOL_CHOICES, blank=True)
    privacy_consent_at = models.DateTimeField('개인정보 수집·이용 동의 시각', null=True, blank=True)

    def __str__(self):
        return self.username


class Friendship(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_links')
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_of_links')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'friend'), name='unique_user_friend_link')]


class FriendCheer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_cheers_sent')
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_cheers_received')
    date = models.DateField(default=timezone.localdate)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'friend', 'date'), name='unique_daily_friend_cheer')]


class MiniGameRound(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mini_game_rounds')
    created_at = models.DateTimeField(auto_now_add=True)
    points_claimed = models.BooleanField(default=False)
