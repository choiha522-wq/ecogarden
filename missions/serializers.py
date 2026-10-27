from django.utils import timezone
from rest_framework import serializers

from .models import Mission, QuizQuestion


class MissionSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = (
            'id', 'title', 'description', 'category', 'mission_type', 'emoji',
            'reward_points', 'reward_tickets', 'reward_water', 'reward_sunlight', 'requires_photo',
            'ai_assisted', 'completed',
        )

    def get_completed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.submissions.filter(user=user, approved=True, date=timezone.localdate()).exists()


class QuizQuestionSerializer(serializers.ModelSerializer):
    """학생에게 보여주는 문제. 정답/해설은 일부러 빼고 보냄 (제출 후에만 공개)."""
    choices = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ('id', 'text', 'choices')
