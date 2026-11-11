from django.urls import path

from .views import WeeklyGoalView, MissionListView, MissionSubmitView, QuizDetailView, QuizSubmitView, PhotoGalleryView, FinalPracticeView

urlpatterns = [
    path('weekly/', WeeklyGoalView.as_view(), name='weekly-goal'),
    path('', MissionListView.as_view(), name='mission-list'),
    path('gallery/', PhotoGalleryView.as_view(), name='photo-gallery'),
    path('final-practice/', FinalPracticeView.as_view(), name='final-practice'),
    path('<int:mission_id>/submit/', MissionSubmitView.as_view(), name='mission-submit'),
    path('<int:mission_id>/quiz/', QuizDetailView.as_view(), name='quiz-detail'),
    path('<int:mission_id>/quiz/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
]
