from django.urls import path

from .views import WeeklyGoalView, MissionListView, MissionSubmitView, RecordMissionSubmitView, ObservationSummaryView, QuizDetailView, QuizSubmitView, ObservationJournalView

urlpatterns = [
    path('weekly/', WeeklyGoalView.as_view(), name='weekly-goal'),
    path('', MissionListView.as_view(), name='mission-list'),
    path('observations/summary/', ObservationSummaryView.as_view(), name='observation-summary'),
    path('journal/', ObservationJournalView.as_view(), name='observation-journal'),
    path('<int:mission_id>/submit/', MissionSubmitView.as_view(), name='mission-submit'),
    path('<int:mission_id>/record/submit/', RecordMissionSubmitView.as_view(), name='record-submit'),
    path('<int:mission_id>/quiz/', QuizDetailView.as_view(), name='quiz-detail'),
    path('<int:mission_id>/quiz/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
]