from io import BytesIO

from django.utils import timezone
from PIL import Image, ImageOps
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import sim
from .ai import AIUnavailable, identify_plant
from .models import GardenPlot, GardenProgress, SeedType, UserSeedInventory
from .progression import grid_size_for_level, plot_count_for_level, progress_payload, unlocked_slot_indexes
from .serializers import GardenPlotSerializer, SeedTypeSerializer, UserSeedInventorySerializer


def garden_state(user, detail=''):
    """정원 전체 상태(생태 시뮬레이션 + 레벨에 열린 땅 + 보유 아이템). 모든 정원 API가 이 모양으로 응답해요."""
    plots = list(GardenPlot.objects.filter(user=user).select_related('seed_type'))
    progress, _ = GardenProgress.objects.get_or_create(user=user)
    size = grid_size_for_level(progress.level)
    opened = set(unlocked_slot_indexes(size))
    poll = sim.pollination_bonus(plots)
    ctx = {'sun': sim.sun_levels(plots, size), 'poll': poll, 'unlocked_slot_indexes': opened}
    return {
        'detail': detail,
        'progression': progress_payload(progress),
        'plot_count': plot_count_for_level(progress.level),
        'grid_size': size,
        'max_plot_count': 25,
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
        'photo_plants_left': sim.photo_plants_left(user),     # 오늘 사진으로 더 심을 수 있는 횟수
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
        if slot_index not in unlocked_slot_indexes(grid_size_for_level(progress.level)):
            return _bad(f'정원 레벨 {progress.level}에서 열리는 땅이에요.')

        inv = UserSeedInventory.objects.filter(
            user=request.user, seed_type__key=request.data.get('seed_key'), quantity__gt=0,
        ).first()
        if inv is None:
            return _bad('보유한 씨앗이 없어요.')
        if inv.seed_type.unlock_level > progress.level:
            return _bad(f'{inv.seed_type.name} 도감은 정원 레벨 {inv.seed_type.unlock_level}에서 열려요.')

        inv.quantity -= 1
        inv.save(update_fields=['quantity'])
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


def _prepare_image(upload):
    """업로드된 사진을 안전하게 줄여서 JPEG 바이트로 돌려줘요. (위치 정보 같은 EXIF는 이 과정에서 사라져요)"""
    if upload.size > 12 * 1024 * 1024:
        raise ValueError('사진이 너무 커요.')
    img = ImageOps.exif_transpose(Image.open(upload)).convert('RGB')
    img.thumbnail((1024, 1024))
    buf = BytesIO()
    img.save(buf, 'JPEG', quality=85)
    return buf.getvalue()


class PlantPhotoView(APIView):
    """
    사진 속 식물을 AI가 알아봐서, 그 종을 정원의 빈 화분에 진짜 식물(새싹)로 심어요.
    상점에서 산 식물과 똑같이 물·햇빛·영양분을 주며 키울 수 있어요.
    사진은 서버에 저장하지 않아요 (AI가 보고 바로 버려요).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slot_index):
        upload = request.data.get('photo')
        if upload is None:
            return _bad('사진이 필요해요.')

        user = request.user
        sim.advance(user)
        plot = GardenPlot.objects.filter(user=user, slot_index=slot_index).first()
        if plot is None or not plot.is_empty:
            return _bad('빈 화분이 아니에요.')
        progress, _ = GardenProgress.objects.get_or_create(user=user)
        if slot_index not in unlocked_slot_indexes(grid_size_for_level(progress.level)):
            return _bad(f'정원 레벨 {progress.level}에서 열리는 땅이에요.')
        if sim.photo_plants_left(user) < 1:
            return _bad(f'오늘은 사진으로 심을 수 있는 횟수({sim.PHOTO_PLANT_DAILY}번)를 다 썼어요. 내일 다시 해봐요!')

        try:
            image = _prepare_image(upload)
        except Exception:
            return _bad('사진 파일을 읽을 수 없어요. 다른 사진으로 해볼까요?')

        try:
            found = identify_plant(image)
        except AIUnavailable:
            return Response({'detail': 'AI 키가 설정되지 않았어요. 프로젝트 폴더의 .env에 GEMINI_API_KEY를 넣고 서버를 다시 시작해 주세요.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            return Response({'detail': 'AI가 잠시 바빠요. 조금 뒤에 다시 시도해 주세요.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        species = SeedType.objects.filter(key=found['species_key']).first() if found['species_key'] else None
        if not found['is_plant'] or species is None:
            return _bad('어떤 식물인지 알아보지 못했어요. 나무나 꽃이 잘 보이게 가까이에서 다시 찍어볼까요?')
        if species.unlock_level > progress.level:
            return _bad(f'{species.name} 도감은 정원 레벨 {species.unlock_level}에서 열려요.')

        plot.seed_type = species
        plot.growth_stage = 1                 # 새싹으로 시작해요
        plot.growth_progress = 0
        plot.completion_recorded = False
        plot.stress = 0
        plot.stress_reason = ''
        plot.death_reason = ''
        plot.save()

        today = timezone.localdate()
        if user.photo_plant_date != today:
            user.photo_plant_date, user.photo_plant_count = today, 0
        user.photo_plant_count += 1
        user.save(update_fields=['photo_plant_date', 'photo_plant_count'])

        similar = '' if found['match'] == 'exact' else ' (목록에서 가장 비슷한 종으로 심었어요)'
        data = garden_state(user, f"🔍 AI가 {species.name}(으)로 알아봤어요!{similar}")
        data['identified'] = {
            'key': species.key, 'name': species.name, 'emoji': species.emoji, 'kind': species.kind,
            'match': found['match'], 'label': found['label'], 'reason': found['reason'],
        }
        return Response(data)
