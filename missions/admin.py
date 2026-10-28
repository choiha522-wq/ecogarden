from django.contrib import admin

from .models import DailyMission, Mission, MissionSubmission, ObservationEntry, ObservationJournal, QuizQuestion


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 0


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'mission_type', 'category', 'reward_points', 'is_active')
    list_filter = ('mission_type', 'category', 'is_active')
    inlines = [QuizQuestionInline]


admin.site.register(MissionSubmission)
admin.site.register(DailyMission)
admin.site.register(ObservationJournal)
admin.site.register(ObservationEntry)
