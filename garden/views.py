from django.utils import timezone
from django.db import transaction
from django.db.models import F
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import sim
from .models import GardenPlot, GardenProgress, SeedType, UserSeedInventory, PlantCollection
from .progression import grid_size_for_level, plot_count_for_level, progress_payload, unlocked_slot_indexes
from .serializers import GardenPlotSerializer, SeedTypeSerializer, UserSeedInventorySerializer


def garden_state(user, detail=''):
    """정원 전체 상태(생태 시뮬레이션 + 레벨에 열린 땅 + 보유 아이템). 모든 정원 API가 이 모양으로 응답해요."""
    plots = list(GardenPlot.objects.filter(user=user).select_related('seed_type'))
    progress, _ = GardenProgress.objects.get_or_create(user=user)
    size = grid_size_for_level(progress.level)
    opened = set(unlocked_slot_indexes(size, progress.level))
    opened.update(p.slot_index for p in plots if p.seed_type_id or p.photo)
    poll = sim.pollination_bonus(plots)
    ctx = {'sun': sim.sun_levels(plots, size), 'poll': poll, 'unlocked_slot_indexes': opened}
    return {
        'detail': detail,
        'progression': progress_payload(progress),
        'collection': list(PlantCollection.objects.filter(user=user).values('seed_type__key', 'harvested_count')),
        'points': user.points,
        'plot_count': len(opened),
        'grid_size': size,
        'max_plot_count': 49,
        'co2_ppm': round(user.co2_ppm, 1),
        'co2_baseline': sim.CO2_BASELINE,
        'co2_limit': sim.CO2_LIMIT,
        'step_minutes': sim.step_minutes(),
        'nutrients': user.nutrients,
        'microbes': user.microbes,
        'water_drops': user.water_drops,                 # 보유 물방울
        'sunlight': user.sunlight,                       # 보유 햇빛 조각
        'water_cap': sim.WATER_CAP,
        'water_next_seconds': sim.water_next_seconds(user),   # 다음 물방울까지 남은 시간(초), 가득이면 null
        'diversity': sim.diversity(plots),               # 살아있는 식물 종류 수
        'pollination': round((poll - 1) * 100),          # 꽃가루받이 성장 보너스(%)
        'plots': GardenPlotSerializer(plots, many=True, context=ctx).data,
    }


def _bad(msg):
    return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)


def _living_plot(user, slot_index):
    """살아있는 나무가 심어진 화분을 돌려줘요. 아니면 (None, 에러 응답)."""
    sim.advance(user)
    plot = GardenPlot.objects.filter(user=user, slot_index=slot_index).first()
    if plot is None or plot.seed_type_id is None:
        return None, _bad('심어진 식물이 없어요.')
    if plot.is_dead:
        return None, _bad('시든 나무예요. 뽑아서 정리해 주세요.')
    return plot, None


class GardenListView(APIView):
    """내 정원 상태 조회. 조회할 때마다 지난 시간만큼 정원이 자동으로 계산돼요."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sim.advance(request.user)
        return Response(garden_state(request.user))


class SpeciesListView(generics.ListAPIView):
    """모든 씨앗(나무·꽃) 종류. 로그인하지 않아도 볼 수 있어요 (상점 구경용)."""
    queryset = SeedType.objects.all().order_by('kind', 'difficulty', 'id')
    serializer_class = SeedTypeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        context['catalog'] = True
        context['collected_keys'] = set(PlantCollection.objects.filter(user=user).values_list('seed_type__key', flat=True)) if user.is_authenticated else set()
        context['garden_level'] = (GardenProgress.objects.filter(user=user).values_list('level', flat=True).first() or 1) if user.is_authenticated else 1
        return context


class SeedInventoryView(APIView):
    """보유 씨앗 목록."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = UserSeedInventory.objects.filter(user=request.user, quantity__gt=0)
        return Response(UserSeedInventorySerializer(qs, many=True).data)


class PlantSeedView(APIView):
    """빈 화분에 씨앗 심기."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        sim.advance(request.user)
        plot = GardenPlot.objects.filter(user=request.user, slot_index=slot_index).first()
        if plot is None or not plot.is_empty:
            return _bad('빈 화분이 아니에요.')
        progress, _ = GardenProgress.objects.get_or_create(user=request.user)
        if slot_index not in unlocked_slot_indexes(grid_size_for_level(progress.level), progress.level):
            return _bad(f'정원 레벨 {progress.level}에서 열리는 땅이에요.')

        inv = UserSeedInventory.objects.filter(
            user=request.user, seed_type__key=request.data.get('seed_key'), quantity__gt=0,
        ).first()
        if inv is None:
            return _bad('보유한 씨앗이 없어요.')
        # Previously owned seeds remain usable after the unlock rules change.

        inv.quantity -= 1
        inv.save(update_fields=['quantity'])
        PlantCollection.objects.get_or_create(user=request.user, seed_type=inv.seed_type)
        plot.seed_type = inv.seed_type
        plot.growth_stage = 0
        plot.growth_progress = 0
        plot.completion_recorded = False
        plot.stress = 0
        plot.stress_reason = ''
        plot.death_reason = ''
        plot.save()
        return Response(garden_state(request.user, f'{inv.seed_type.name} 씨앗을 심었어요'))


class WaterPlotView(APIView):
    """물 주기: 물방울 1개를 써서 흙의 수분을 채워요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        plot, err = _living_plot(request.user, slot_index)
        if err:
            return err
        user = request.user
        if user.water_drops < 1:
            return _bad('물방울이 없어요. 30분마다 1개씩 모이고, 미션이나 상점에서도 얻을 수 있어요.')
        if plot.water >= 100:
            return _bad('물이 이미 가득해요.')
        user.water_drops -= 1
        user.save(update_fields=['water_drops'])
        plot.water = min(100.0, plot.water + sim.WATER_AMOUNT)
        plot.save(update_fields=['water'])
        return Response(garden_state(user, '💧 물을 줬어요'))


class SunlightPlotView(APIView):
    """햇빛 주기: 햇빛 조각 1개를 써서 그늘 때문에 모자란 햇빛을 채워요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        plot, err = _living_plot(request.user, slot_index)
        if err:
            return err
        user = request.user
        if user.sunlight < 1:
            return _bad('햇빛 조각이 없어요. 사진 미션을 하거나 상점에서 구할 수 있어요.')
        progress, _ = GardenProgress.objects.get_or_create(user=user)
        size = grid_size_for_level(progress.level)
        ambient = sim.sun_levels(list(GardenPlot.objects.filter(user=user).select_related('seed_type')), size)[plot.slot_index]
        if min(100.0, ambient + plot.sun_boost) >= 100:
            return _bad('햇빛이 이미 충분해요. 그늘진 칸에 써 보세요.')
        user.sunlight -= 1
        user.save(update_fields=['sunlight'])
        plot.sun_boost = min(100.0, plot.sun_boost + sim.SUN_BOOST_AMOUNT)
        plot.save(update_fields=['sun_boost'])
        return Response(garden_state(user, '☀️ 햇빛을 채웠어요'))


class FeedPlotView(APIView):
    """영양제 주기: 흙의 영양분을 채워요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        plot, err = _living_plot(request.user, slot_index)
        if err:
            return err
        user = request.user
        if user.nutrients < 1:
            return _bad('영양제가 없어요.')
        if plot.nutrients >= 100:
            return _bad('영양분이 이미 가득해요.')
        user.nutrients -= 1
        user.save(update_fields=['nutrients'])
        plot.nutrients = min(100.0, plot.nutrients + sim.FEED_AMOUNT)
        plot.save(update_fields=['nutrients'])
        return Response(garden_state(user, '🧪 영양분을 채웠어요'))


class MicrobePlotView(APIView):
    """미생물제 주기: 흙 속 미생물이 늘어나 나무가 빨리 자라고 영양분도 만들어져요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        plot, err = _living_plot(request.user, slot_index)
        if err:
            return err
        user = request.user
        if user.microbes < 1:
            return _bad('미생물제가 없어요.')
        if plot.microbes >= 100:
            return _bad('미생물이 이미 가득해요.')
        user.microbes -= 1
        user.save(update_fields=['microbes'])
        plot.microbes = min(100.0, plot.microbes + sim.MICROBE_AMOUNT)
        plot.save(update_fields=['microbes'])
        return Response(garden_state(user, '🦠 미생물이 늘어났어요'))


class DigPlotView(APIView):
    """화분을 비움(뽑기). 식물만 사라지고 흙 상태는 그대로예요."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        sim.advance(request.user)
        plot = GardenPlot.objects.filter(user=request.user, slot_index=slot_index).first()
        if plot is None:
            return Response({'detail': '화분이 없어요.'}, status=status.HTTP_404_NOT_FOUND)
        plot.reset_plant()
        plot.save()
        return Response(garden_state(request.user, '화분을 비웠어요'))


class HarvestPlotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        # User row serializes harvest/reward requests from this account.
        with transaction.atomic():
            user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
            sim.advance(user)
            plot = GardenPlot.objects.select_for_update(of=('self',)).filter(user=user, slot_index=slot_index).select_related('seed_type').first()
            if not plot or not plot.seed_type_id or plot.is_dead or plot.growth_stage < 4:
                return _bad('살아 있는 성장 완료 식물만 수확할 수 있어요.')
            collection, _ = PlantCollection.objects.get_or_create(user=user, seed_type=plot.seed_type)
            PlantCollection.objects.filter(pk=collection.pk).update(harvested_count=F('harvested_count') + 1)
            if not plot.completion_recorded:
                from .progression import record_completed_plants
                record_completed_plants(user, [plot.seed_type.difficulty])
            name = plot.seed_type.name
            user.points += 20
            user.save(update_fields=['points'])
            plot.reset_plant()
            plot.save()
        return Response(garden_state(user, f'✨ {name} 수확! 성과 도감에 기록하고 +20P를 받았어요.'))


class GardenStyleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        theme = request.data.get('theme')
        action = request.data.get('action')
        if theme not in ('spring', 'summer', 'autumn', 'winter'):
            return _bad('계절을 선택해 주세요.')
        with transaction.atomic():
            user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
            progress, _ = GardenProgress.objects.select_for_update().get_or_create(user=user)
            favorite = getattr(user, 'favorite_season', 'spring') or 'spring'
            owned = set(progress.owned_themes or []) | {favorite}
            if action == 'buy':
                if theme not in owned:
                    if user.points < 40:
                        return _bad('계절 꾸미기 구매에 40P가 필요해요.')
                    user.points -= 40
                    user.save(update_fields=['points'])
                    owned.add(theme)
                    progress.owned_themes = sorted(owned)
                    progress.save(update_fields=['owned_themes'])
                    detail = '계절 꾸미기를 구매했어요.'
                else:
                    detail = '이미 보유한 계절 꾸미기예요.'
                return Response(garden_state(user, detail))
            if theme not in owned:
                if user.points < 40:
                    return _bad('계절 꾸미기 구매에 40P가 필요해요.')
                user.points -= 40
                user.save(update_fields=['points'])
                owned.add(theme)
            progress.theme = theme
            progress.owned_themes = sorted(owned)
            progress.save(update_fields=['theme', 'owned_themes'])
        return Response(garden_state(user, '계절 배경을 적용했어요.'))
