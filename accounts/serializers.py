from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .attendance import attendance_state
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    consent = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'region_sido', 'region_sigungu', 'school_level', 'consent')
        extra_kwargs = {
            'region_sido': {'required': True, 'allow_blank': False, 'error_messages': {
                'required': '사는 지역(시·도)을 골라 주세요.', 'blank': '사는 지역(시·도)을 골라 주세요.',
                'invalid_choice': '사는 지역(시·도)을 골라 주세요.', 'null': '사는 지역(시·도)을 골라 주세요.'}},
            'region_sigungu': {'required': False},
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


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """마이페이지에서 고칠 수 있는 정보 (지역, 학교급)."""
    class Meta:
        model = User
        fields = ('region_sido', 'region_sigungu', 'school_level')
        extra_kwargs = {'region_sido': {'allow_blank': False}}
