from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .attendance import claim_attendance
from .models import FriendCheer, Friendship, MiniGameRound, User
from .serializers import ProfileUpdateSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """회원가입. 로그인은 simplejwt의 TokenObtainPairView(/api/auth/login/)를 그대로 사용."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """내 정보 + 현재 보유 포인트/티켓/영양제 조회. 프로토타입 헤더의 칩(chip) 영역에 대응."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from garden.sim import refill_water
        refill_water(request.user)  # 시간이 지나 모인 물방울 반영
        if not request.user.friend_code:
            request.user.friend_code = f'GREEN-{request.user.id:04d}'
            request.user.save(update_fields=['friend_code'])
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        """마이페이지의 아이디·좋아하는 계절·칭호·프로필 이미지를 수정해요."""
        old_season = request.user.favorite_season
        ser = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        from garden.models import GardenProgress
        progress, _ = GardenProgress.objects.get_or_create(user=user)
        owned = set(progress.owned_themes or [])
        changed = False
        if user.favorite_season != old_season:
            owned.update((old_season, user.favorite_season))
            progress.theme = user.favorite_season
            changed = True
        # 예전 버전에서 선호 계절만 바뀌고 소유 목록이 갱신되지 않은 계정도 보정해요.
        if user.favorite_season not in owned:
            owned.add(user.favorite_season)
            changed = True
        if sorted(owned) != sorted(progress.owned_themes or []):
            progress.owned_themes = sorted(owned)
            changed = True
        if changed:
            progress.save(update_fields=['owned_themes', 'theme'])
        return Response(UserSerializer(request.user).data)


class ConsumeTicketView(APIView):
    """미니게임 시작 전 티켓 1장 차감. index.html의 play()에서 S.tk-- 하던 부분."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if user.tickets < 1:
                return Response({'detail': '티켓이 없어요.'}, status=400)
            user.tickets -= 1
            user.save(update_fields=['tickets'])
            round = MiniGameRound.objects.create(user=user)
        data = UserSerializer(user).data
        data['game_round_id'] = str(round.pk)
        return Response(data)


class FinishMiniGameView(APIView):
    """사용한 티켓에 연결된 게임 1회에 한해서 점수를 포인트로 바꿔요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            round_id = UUID(str(request.data.get('game_round_id')))
            score = request.data.get('score')
            game = request.data.get('game')
            if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > 10000:
                raise ValueError
            if game not in ('dodge', 'tetris'):
                raise ValueError
            with transaction.atomic():
                round = MiniGameRound.objects.select_for_update().get(pk=round_id, user=request.user)
                if round.points_claimed:
                    return Response({'detail': '이미 보상을 받은 게임이에요.'}, status=400)
                user = User.objects.select_for_update().get(pk=request.user.pk)
                points = min(30, score * (2 if game == 'dodge' else 1))
                user.points += points
                user.save(update_fields=['points'])
                round.points_claimed = True
                round.save(update_fields=['points_claimed'])
            return Response({'points': user.points, 'earned': points})
        except (ValueError, TypeError, MiniGameRound.DoesNotExist):
            return Response({'detail': '게임 결과가 올바르지 않아요.'}, status=400)


class FriendsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from garden.models import GardenPlot, GardenProgress
        from garden.progression import grid_size_for_level, plot_count_for_level, unlocked_slot_indexes
        links = Friendship.objects.filter(user=request.user).select_related('friend').order_by('friend__username')
        friends = [link.friend for link in links]
        plots = GardenPlot.objects.filter(user__in=friends).select_related('seed_type').order_by('slot_index')
        by_user = {friend.id: [None] * 25 for friend in friends}
        types = {friend.id: [None] * 25 for friend in friends}
        progress_by_user = {p.user_id: p for p in GardenProgress.objects.filter(user__in=friends)}
        for friend in friends:
            progress_by_user.setdefault(friend.id, None)
        plot_counts = {friend.id: plot_count_for_level(progress_by_user[friend.id].level if progress_by_user[friend.id] else 1) for friend in friends}
        allowed_by_user = {friend.id: set(unlocked_slot_indexes(5, progress_by_user[friend.id].level if progress_by_user[friend.id] else 1)) for friend in friends}
        for plot in plots:
            if plot.seed_type_id or plot.photo:
                allowed_by_user[plot.user_id].add(plot.slot_index)
            if plot.slot_index in allowed_by_user[plot.user_id] and plot.seed_type_id and not plot.death_reason:
                by_user[plot.user_id][plot.slot_index] = plot.growth_stage
                types[plot.user_id][plot.slot_index] = plot.seed_type.key
        today = timezone.localdate()
        cheered = set(FriendCheer.objects.filter(user=request.user, date=today).values_list('friend_id', flat=True))
        return Response([{'id': f.id, 'n': f.username, 'e': '🌱', 'code': f.friend_code,
                          'plots': by_user[f.id], 'types': types[f.id], 'plot_count': len(allowed_by_user[f.id]), 'unlocked_slots': sorted(allowed_by_user[f.id]),
                          'garden_level': progress_by_user[f.id].level if progress_by_user[f.id] else 1, 'ch': f.id in cheered}
                         for f in friends])

    def post(self, request):
        code = str(request.data.get('friend_code', '')).strip().upper()
        friend = User.objects.filter(friend_code=code).first()
        if not friend:
            return Response({'detail': '없는 친구 코드예요.'}, status=404)
        if friend.pk == request.user.pk:
            return Response({'detail': '내 친구 코드는 추가할 수 없어요.'}, status=400)
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                link, created = Friendship.objects.get_or_create(user=user, friend=friend)
                Friendship.objects.get_or_create(user=friend, friend=user)
                if not created:
                    return Response({'detail': '이미 친구예요.'}, status=400)
                user.points += 10
                user.save(update_fields=['points'])
            return Response({'detail': f'{friend.username}님을 친구로 추가했어요. +10P', 'points': user.points}, status=201)
        except IntegrityError:
            return Response({'detail': '이미 친구예요.'}, status=400)


class CheerFriendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, friend_id):
        friend = User.objects.filter(pk=friend_id).first()
        if not friend or not Friendship.objects.filter(user=request.user, friend=friend).exists():
            return Response({'detail': '친구를 찾을 수 없어요.'}, status=404)
        try:
            with transaction.atomic():
                locked_users = {
                    item.pk: item for item in User.objects.select_for_update()
                    .filter(pk__in=sorted((request.user.pk, friend.pk))).order_by('pk')
                }
                user = locked_users[request.user.pk]
                friend = locked_users[friend.pk]
                FriendCheer.objects.create(user=user, friend=friend, date=timezone.localdate())
                user.points += 5
                friend.points += 5
                User.objects.bulk_update([user, friend], ['points'])
            return Response({'detail': '응원했어요! 두 사람 모두 ⭐ +5P',
                             'points': user.points, 'friend_points': friend.points})
        except IntegrityError:
            return Response({'detail': '오늘은 이미 응원했어요.'}, status=400)


class AttendanceView(APIView):
    """오늘 출석 보상 받기."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        result = claim_attendance(request.user)
        if result is None:
            return Response({'detail': '오늘은 이미 출석했어요.'}, status=400)
        extra = ' + 🎟️ 티켓 1장' if result['ticket'] else ''
        data = UserSerializer(request.user).data
        data.update({'detail': f"🎁 {result['day']}일차 출석! +{result['reward']}P{extra}", **result})
        return Response(data)


class TutorialStartView(APIView):
    """Atomically claim the one-time tutorial for the authenticated account.

    Mark at first display, not at completion: refreshing, skipping, or signing
    in on another device must not automatically replay the tutorial.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        changed = User.objects.filter(pk=request.user.pk, tutorial_seen_at__isnull=True).update(
            tutorial_seen_at=timezone.now(),
        )
        return Response({'show_tutorial': changed == 1})
