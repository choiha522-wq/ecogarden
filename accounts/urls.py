from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (AttendanceView, CheerFriendView, ConsumeTicketView, FinishMiniGameView,
                    FriendsView, RegisterView, MeView, TutorialStartView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='login-refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('tutorial/start/', TutorialStartView.as_view(), name='tutorial-start'),
    path('consume-ticket/', ConsumeTicketView.as_view(), name='consume-ticket'),
    path('mini-game/finish/', FinishMiniGameView.as_view(), name='mini-game-finish'),
    path('friends/', FriendsView.as_view(), name='friends'),
    path('friends/<int:friend_id>/cheer/', CheerFriendView.as_view(), name='friend-cheer'),
    path('attendance/', AttendanceView.as_view(), name='attendance'),
]
