from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .attendance import attendance_state
from .models import User, SEASON_CHOICES
from .profile import avatar_emoji, avatar_options, garden_level, title_options


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    consent = serializers.BooleanField(write_only=True)
    favorite_season = serializers.ChoiceField(choices=SEASON_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'school_level', 'favorite_season', 'consent')
        extra_kwargs = {
            'school_level': {'required': False},
        }

    def validate_consent(self, value):
        if value is not True:
            raise serializers.ValidationError('개인정보 수집·이용에 동의해 주세요.')
        return value

    def create(self, validated_data):
        validated_data.pop('consent')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, privacy_consent_at=timezone.now(), points=30, **validated_data)
        from garden.models import GardenProgress
        GardenProgress.objects.create(user=user, theme=user.favorite_season, owned_themes=[user.favorite_season])
        # 첫날부터 상점·정원을 경험할 수 있는 시작 꾸러미 (씨앗 데이터가 준비된 경우)
        from garden.models import SeedType, UserSeedInventory
        starter_seed = SeedType.objects.filter(key='pine').first()
        if starter_seed:
            UserSeedInventory.objects.get_or_create(user=user, seed_type=starter_seed, defaults={'quantity': 1})
        # 친구 코드는 가입 시 자동 발급 (프로토타입의 GREEN-xxxx 형식 참고)
        user.friend_code = f'GREEN-{user.id:04d}'
        user.save(update_fields=['friend_code'])
        return user


class UserSerializer(serializers.ModelSerializer):
    attendance_streak = serializers.SerializerMethodField()
    attendance_claimed_today = serializers.SerializerMethodField()
    profile_avatar_emoji = serializers.SerializerMethodField()
    profile_title_options = serializers.SerializerMethodField()
    profile_avatar_options = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'points', 'tickets', 'nutrients', 'microbes', 'water_drops', 'sunlight',
            'friend_code', 'school_level', 'date_joined',
            'favorite_season', 'profile_title', 'profile_avatar', 'profile_avatar_emoji',
            'profile_title_options', 'profile_avatar_options',
            'attendance_streak', 'attendance_claimed_today',
        )
        read_only_fields = fields

    def get_attendance_streak(self, obj):
        return attendance_state(obj)['streak']

    def get_attendance_claimed_today(self, obj):
        return attendance_state(obj)['claimed']

    def get_profile_avatar_emoji(self, obj):
        return avatar_emoji(obj.profile_avatar)

    def get_profile_title_options(self, obj):
        return title_options(garden_level(obj))

    def get_profile_avatar_options(self, obj):
        return avatar_options(garden_level(obj))


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """아이디, 계절, 해금된 칭호·프로필 이미지를 수정해요."""
    class Meta:
        model = User
        fields = ('username', 'favorite_season', 'profile_title', 'profile_avatar', 'school_level')
        extra_kwargs = {
            'username': {'required': False},
            'favorite_season': {'required': False},
            'profile_title': {'required': False},
            'profile_avatar': {'required': False},
            'school_level': {'required': False},
        }

    def validate_username(self, value):
        value = value.strip()
        User._meta.get_field('username').run_validators(value)
        if User.objects.exclude(pk=self.instance.pk).filter(username__iexact=value).exists():
            raise serializers.ValidationError('이미 사용 중인 아이디예요.')
        return value

    def validate_profile_title(self, value):
        level = garden_level(self.instance)
        if not any(item['title'] == value and item['unlocked'] for item in title_options(level)):
            raise serializers.ValidationError('아직 해금되지 않은 칭호예요.')
        return value

    def validate_profile_avatar(self, value):
        level = garden_level(self.instance)
        if not any(item['key'] == value and item['unlocked'] for item in avatar_options(level)):
            raise serializers.ValidationError('아직 해금되지 않은 프로필 이미지예요.')
        return value
