from django.urls import path

from .views import MissionListView, MissionSubmitView, RecordMissionSubmitView, ObservationSummaryView, QuizDetailView, QuizSubmitView

urlpatterns = [
    path('', MissionListView.as_view(), name='mission-list'),
    path('observations/summary/', ObservationSummaryView.as_view(), name='observation-summary'),
    path('<int:mission_id>/submit/', MissionSubmitView.as_view(), name='mission-submit'),
    path('<int:mission_id>/record/submit/', RecordMissionSubmitView.as_view(), name='record-submit'),
    path('<int:mission_id>/quiz/', QuizDetailView.as_view(), name='quiz-detail'),
    path('<int:mission_id>/quiz/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
]