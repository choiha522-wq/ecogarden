from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Mission(models.Model):
    CATEGORY_CHOICES = [
        ('observation', '관찰'),
        ('microbe', '미생물'),
        ('local', '지역'),
    ]
    # 미션 종류. 새 종류(예: 관찰 일지)를 만들 땐 여기에 한 줄 추가하고 views.py에 처리만 붙이면 돼요.
    TYPE_CHOICES = [
        ('photo', '사진 인증'),
        ('quiz', '퀴즈'),
        ('record', '관찰 기록'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    mission_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='photo')
    emoji = models.CharField(max_length=8, default='🌱')
    reward_points = models.PositiveIntegerField(default=20)
    reward_tickets = models.PositiveIntegerField(default=1)
    reward_water = models.PositiveIntegerField(default=1)      # 보상으로 주는 물방울
    reward_sunlight = models.PositiveIntegerField(default=0)   # 보상으로 주는 햇빛 조각 (사진 미션: 밖에 나가 햇빛을 쬔 보상!)
    requires_photo = models.BooleanField(default=True)
    ai_assisted = models.BooleanField(
        default=False,
        help_text='사진 인식 등 AI 검증이 필요한 미션인지 여부 (사진 인증 미션에서만 의미 있음)',
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class DailyMission(models.Model):
    """
    계정별 오늘의 미션 목록. 처음 미션을 열 때 계정과 날짜를 기준으로 뽑아 저장해요.
    """
    date = models.DateField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_missions')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='daily_entries')

    class Meta:
        unique_together = ('date', 'user', 'mission')

    def __str__(self):
        return f'{self.date} {self.mission}'


class QuizQuestion(models.Model):
    """퀴즈 미션에 딸린 문제. 관리자 페이지에서 미션 화면 아래에 바로 추가할 수 있어요."""
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveSmallIntegerField(default=0)
    text = models.CharField('문제', max_length=200)
    choice1 = models.CharField('보기 1', max_length=100)
    choice2 = models.CharField('보기 2', max_length=100)
    choice3 = models.CharField('보기 3', max_length=100, blank=True)
    choice4 = models.CharField('보기 4', max_length=100, blank=True)
    answer = models.PositiveSmallIntegerField('정답 번호(1~4)')
    explanation = models.CharField('해설', max_length=300, blank=True)

    class Meta:
        ordering = ['order', 'id']

    @property
    def choices(self):
        return [c for c in (self.choice1, self.choice2, self.choice3, self.choice4) if c]

    def clean(self):
        if not 1 <= (self.answer or 0) <= len(self.choices):
            raise ValidationError('정답 번호가 보기 개수를 벗어났어요.')

    def __str__(self):
        return self.text


class MissionSubmission(models.Model):
    """
    학생의 미션 수행 기록.
    - 사진 인증은 사진을 메모리에서 정규화·검증하며 업로드 원본은 저장하지 않아요.
    - 퀴즈는 기준 점수 이상, 관찰 기록은 글자 수 기준을 통과하면 approved예요.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mission_submissions')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='submissions')
    photo = models.ImageField(upload_to='mission_photos/', blank=True, null=True)
    ai_label = models.CharField(max_length=100, blank=True, help_text='AI가 인식한 식물/곤충 이름 등')
    observation_region = models.CharField(max_length=10, blank=True)
    observation_habitat = models.CharField(max_length=20, blank=True, choices=[('garden', '정원/화분'), ('school', '학교'), ('park', '공원/화단'), ('forest', '숲'), ('other', '기타')])
    observation_sign = models.CharField(max_length=20, blank=True, choices=[('leaf', '잎'), ('flower', '꽃'), ('fruit_seed', '열매/씨앗'), ('insect', '곤충'), ('bird', '새'), ('soil', '흙/낙엽'), ('other', '기타')])
    approved = models.BooleanField(default=False)
    date = models.DateField(default=timezone.localdate)  # 어느 날의 미션을 수행했는지 (매일 새로 도전할 수 있어요)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'mission', 'date')

    def __str__(self):
        return f'{self.user} - {self.mission}'


class ObservationJournal(models.Model):
    """사용자마다 한 식물을 정해 매일 관찰 기록을 쌓는 개인 일지."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='observation_journal')
    plant_name = models.CharField(max_length=80, help_text='현실에서 키우는 식물 이름')
    plant_confirmed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ObservationEntry(models.Model):
    """사용자의 개인 관찰 일지. 기록 문장은 해당 사용자에게만 보여요."""
    journal = models.ForeignKey(ObservationJournal, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField(default=timezone.localdate, db_index=True)
    response = models.CharField(max_length=500)
    habitat = models.CharField(max_length=20, choices=[('garden', '정원/화분'), ('school', '학교'), ('park', '공원/화단'), ('forest', '숲'), ('other', '기타')])
    sign = models.CharField(max_length=20, choices=[('leaf', '잎'), ('flower', '꽃'), ('fruit_seed', '열매/씨앗'), ('other', '기타')])

    class Meta:
        constraints = [models.UniqueConstraint(fields=('journal', 'date'), name='unique_daily_observation_entry')]
        ordering = ['-date', '-id']
