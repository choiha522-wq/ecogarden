import math
import random
from io import BytesIO
import logging

from PIL import Image, ImageOps
from django.db import IntegrityError, transaction
from django.db.models import Count
from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .learning import learning_card
from .daily import ensure_daily
from .models import Mission, MissionSubmission, ObservationEntry, ObservationJournal
from .serializers import MissionSerializer
from .services import verify_mission_photo

logger = logging.getLogger(__name__)


def todays_mission(user, mission_id, **extra):
    """오늘의 미션 중에서만 도전할 수 있어요. 자정이 지나 목록이 바뀐 뒤 어제 미션을 내면 안내해요."""
    try:
        return ensure_daily(user=user).get(pk=mission_id, **extra)
    except Mission.DoesNotExist:
        raise ValidationError({'detail': '오늘의 미션이 아니에요. 새로고침해서 새 미션을 확인해 주세요.'})


def grant_reward(user, mission):
    user.points += mission.reward_points
    user.tickets += mission.reward_tickets
    user.water_drops += mission.reward_water
    user.sunlight += mission.reward_sunlight
    user.save(update_fields=['points', 'tickets', 'water_drops', 'sunlight'])


def reward_text(mission):
    parts = [f'+{mission.reward_points}P', f'티켓 +{mission.reward_tickets}']
    if mission.reward_water:
        parts.append(f'💧+{mission.reward_water}')
    if mission.reward_sunlight:
        parts.append(f'☀️+{mission.reward_sunlight}')
    return ', '.join(parts)


class MissionListView(generics.ListAPIView):
    """오늘의 미션 목록. ?category=observation 식으로 필터링. 로그인 안 해도 구경할 수 있어요."""
    serializer_class = MissionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = ensure_daily(user=self.request.user)  # 계정별 오늘 미션
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs


class MissionSubmitView(APIView):
    """
    [사진 인증 미션] 사진을 제출하면 AI(Gemini)가 검증하고, 통과해야만 보상이 지급됩니다.
    퀴즈 미션은 이 API가 아니라 /quiz/ 계열 API를 사용합니다.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mission_id):
        mission = todays_mission(request.user, mission_id)
        if mission.mission_type != 'photo':
            return Response({'detail': '이 미션은 사진 인증 미션이 아니에요.'}, status=status.HTTP_400_BAD_REQUEST)

        photo = request.FILES.get('photo')
        if photo is None:
            return Response({'detail': '사진을 첨부해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        if photo.size > 12 * 1024 * 1024:
            return Response({'detail': '사진은 12MB 이하로 올려 주세요.'}, status=413)
        try:
            image_bytes = _prepare_mission_image(photo)
        except (ValueError, OSError, Image.DecompressionBombError):
            return Response({'detail': '사진 파일을 읽을 수 없어요. JPG나 PNG 사진을 다시 선택해 주세요.'}, status=400)

        try:
            approved, label, ai_message = verify_mission_photo(image_bytes, mission)
        except RuntimeError as exc:
            logger.exception('Photo mission AI configuration error')
            detail = ('AI 키가 설정되지 않았어요. 프로젝트 폴더의 .env에 GEMINI_API_KEY를 넣고 서버를 다시 시작해 주세요.'
                      if 'GEMINI_API_KEY' in str(exc) else '사진 확인 서비스를 사용할 수 없어요. 잠시 후 다시 시도해 주세요.')
            return Response({'detail': detail}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception('Photo mission AI verification failed')
            return Response(
                {'detail': '사진 확인 서비스가 잠시 응답하지 않아요. 잠시 후 다시 제출해 주세요.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        with transaction.atomic():
            user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
            submission, _ = MissionSubmission.objects.select_for_update().get_or_create(
                user=user, mission=mission, date=timezone.localdate(),
            )
            if submission.approved:
                return Response({'detail': '이미 완료한 미션이에요.'}, status=400)
            submission.ai_label = label
            if not approved:
                submission.save(update_fields=['ai_label'])
                return Response({'detail': f'사진이 미션과 맞지 않는 것 같아요. {ai_message}'.strip()}, status=400)
            submission.approved = True
            submission.save(update_fields=['ai_label', 'approved'])
            grant_reward(user, mission)
        request.user.points, request.user.tickets = user.points, user.tickets
        request.user.water_drops, request.user.sunlight = user.water_drops, user.sunlight

        label_part = f' (AI: {submission.ai_label})' if submission.ai_label else ''
        return Response({
            'education': learning_card(mission),
            'detail': f'미션 완료!{label_part} {reward_text(mission)}',
            'points': request.user.points,
            'tickets': request.user.tickets,
            'water_drops': request.user.water_drops,
            'sunlight': request.user.sunlight,
        })


def _prepare_mission_image(upload):
    """파일 크기와 실제 이미지 형식을 확인한 뒤 AI에 보낼 JPEG로 정규화해요."""
    if upload.size > 12 * 1024 * 1024:
        raise ValueError('사진이 너무 커요.')
    image = ImageOps.exif_transpose(Image.open(upload)).convert('RGB')
    image.thumbnail((1280, 1280))
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=88, optimize=True)
    return buffer.getvalue()


class RecordMissionSubmitView(APIView):
    """한 식물을 정해 매일 기록하고 개인 관찰 일지에 저장하는 미션."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mission_id):
        mission = todays_mission(request.user, mission_id, mission_type='record')
        response_text = request.data.get('response', '')
        plant_name = request.data.get('plant_name', '')
        if not isinstance(response_text, str):
            return Response({'detail': '관찰 기록을 입력해 주세요.'}, status=400)
        response_text = response_text.strip()
        if len(response_text) < 15:
            return Response({'detail': '관찰한 내용이나 궁금한 점을 15자 이상 적어 주세요.'}, status=400)
        if len(response_text) > 500:
            return Response({'detail': '관찰 기록은 500자 이내로 적어 주세요.'}, status=400)

        habitat = request.data.get('habitat', '')
        sign = request.data.get('sign', '')
        valid_habitats = {key for key, _ in MissionSubmission._meta.get_field('observation_habitat').choices}
        valid_signs = {'leaf', 'flower', 'fruit_seed', 'other'}
        if habitat not in valid_habitats or sign not in valid_signs:
            return Response({'detail': '장소와 식물에서 관찰한 부분을 선택해 주세요.'}, status=400)

        if not isinstance(plant_name, str):
            return Response({'detail': '현실에서 키우는 식물 이름을 적어 주세요.'}, status=400)
        plant_name = ' '.join(plant_name.split())
        if not plant_name:
            return Response({'detail': '현실에서 키우는 식물 이름을 적어 주세요.'}, status=400)
        if len(plant_name) > 80:
            return Response({'detail': '식물 이름은 80자 이내로 적어 주세요.'}, status=400)
        today = timezone.localdate()
        try:
            with transaction.atomic():
                user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
                submission, _ = MissionSubmission.objects.select_for_update().get_or_create(
                    user=user, mission=mission, date=today,
                )
                if submission.approved:
                    return Response({'detail': '이미 완료한 미션이에요.'}, status=400)

                journal = ObservationJournal.objects.filter(user=user).first()
                if journal is None:
                    if request.data.get('journal_consent') is not True:
                        return Response({'detail': '관찰일지 저장에 동의해 주세요.'}, status=400)
                    journal = ObservationJournal.objects.create(user=user, plant_name=plant_name)
                else:
                    if ObservationEntry.objects.filter(journal=journal, date=today).exists():
                        return Response({'detail': '오늘 관찰일지는 이미 저장했어요.'}, status=400)
                    if not journal.plant_confirmed:
                        # 이전 버전에서 고른 도감 식물명은 현실에서 키우는 식물인지 첫 새 기록에서 확인해요.
                        journal.plant_name = plant_name
                        journal.plant_confirmed = True
                        journal.save(update_fields=['plant_name', 'plant_confirmed'])
                    elif journal.plant_name.casefold() != plant_name.casefold():
                        return Response({'detail': f'이 일지에는 {journal.plant_name}을(를) 기록하고 있어요. 현실에서 같은 식물을 계속 관찰해 주세요.'}, status=400)

                ObservationEntry.objects.create(journal=journal, date=today, response=response_text,
                                                habitat=habitat, sign=sign)
                submission.observation_region = user.region_sido
                submission.observation_habitat = habitat
                submission.observation_sign = sign
                submission.approved = True
                submission.save(update_fields=['observation_region', 'observation_habitat', 'observation_sign', 'approved'])
                grant_reward(user, mission)
            return Response({'education': learning_card(mission), 'detail': f'{plant_name} 관찰일지 저장 완료! {reward_text(mission)}',
                             'points': user.points, 'tickets': user.tickets,
                             'water_drops': user.water_drops, 'sunlight': user.sunlight})
        except IntegrityError:
            return Response({'detail': '관찰일지를 저장하지 못했어요. 이미 오늘 기록했는지 확인해 주세요.'}, status=400)


class ObservationJournalView(APIView):
    """로그인한 사용자 본인의 고정 식물과 관찰일지만 반환해요."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        journal = ObservationJournal.objects.filter(user=request.user).first()
        if journal is None:
            return Response({'target': None, 'entries': []})
        habitats = dict(ObservationEntry._meta.get_field('habitat').choices)
        signs = dict(ObservationEntry._meta.get_field('sign').choices)
        entries = journal.entries.all()
        return Response({
            'target': {'name': journal.plant_name, 'confirmed': journal.plant_confirmed},
            'entries': [{'date': row.date.isoformat(), 'response': row.response,
                         'habitat': habitats.get(row.habitat, ''), 'sign': signs.get(row.sign, '')}
                        for row in entries],
        })


class ObservationSummaryView(APIView):
    """최근 관찰 미션을 개인 식별 없이 지역·장소·관찰 대상별로 집계해요."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        since = timezone.localdate() - timedelta(days=30)
        qs = MissionSubmission.objects.filter(approved=True, mission__mission_type='record', date__gte=since).exclude(observation_sign='').exclude(observation_habitat='')
        signs = list(qs.exclude(observation_sign='').values('observation_sign').annotate(total=Count('id')).order_by('-total'))
        regions = list(qs.values('observation_region').exclude(observation_region='')
                       .annotate(total=Count('id')).filter(total__gte=3).order_by('-total'))
        labels = dict(MissionSubmission._meta.get_field('observation_sign').choices)
        return Response({
            'days': 30, 'total': qs.count(),
            'signs': [{'key': row['observation_sign'], 'label': labels.get(row['observation_sign'], '기타'), 'count': row['total']} for row in signs],
            'regions': [{'name': row['observation_region'], 'count': row['total']} for row in regions],
        })


def needed_to_pass(total):
    """전체 문제의 60% 이상 맞혀야 통과 (3문제면 2개)."""
    return max(1, math.ceil(total * 0.6))


class QuizDetailView(APIView):
    """퀴즈 문제 목록. 정답과 해설은 포함하지 않아요."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, mission_id):
        mission = todays_mission(request.user, mission_id, mission_type='quiz')
        questions = list(mission.questions.all())
        if not questions:
            return Response({'detail': '아직 준비 중인 퀴즈예요.'}, status=status.HTTP_400_BAD_REQUEST)
        # 정답 위치가 특정 번호에 몰리지 않도록 한 퀴즈 안에서 정답 위치를 분산해요.
        max_choices = max((len(question.choices) for question in questions), default=1)
        correct_positions = list(range(max_choices))
        random.shuffle(correct_positions)
        randomized = []
        for index, question in enumerate(questions):
            choices = question.choices
            correct_index = question.answer - 1
            if not choices or not 0 <= correct_index < len(choices):
                return Response({'detail': '퀴즈 보기를 확인할 수 없어요.'}, status=500)
            correct_position = correct_positions[index % len(correct_positions)] % len(choices)
            order = [choice_index for choice_index in range(len(choices)) if choice_index != correct_index]
            random.shuffle(order)
            order.insert(correct_position, correct_index)
            randomized.append({
                'id': question.id,
                'text': question.text,
                'choices': [choices[choice_index] for choice_index in order],
                # 브라우저에서 고른 표시 순번을 서버의 원래 보기 순번으로 변환할 때 사용해요.
                'choice_indexes': order,
            })
        return Response({
            'id': mission.id,
            'title': mission.title,
            'need': needed_to_pass(len(questions)),
            'questions': randomized,
        })


class QuizSubmitView(APIView):
    """
    퀴즈 채점. 요청: {"answers": {"<문제id>": <고른 보기 번호(0부터)>, ...}}
    채점은 서버에서만 하고, 통과했을 때만 정답/해설을 알려주며 보상을 지급해요.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mission_id):
        mission = todays_mission(request.user, mission_id, mission_type='quiz')
        questions = list(mission.questions.all())
        if not questions:
            return Response({'detail': '아직 준비 중인 퀴즈예요.'}, status=status.HTTP_400_BAD_REQUEST)

        answers = request.data.get('answers')
        if not isinstance(answers, dict):
            return Response({'detail': '답안 형식이 올바르지 않아요.'}, status=status.HTTP_400_BAD_REQUEST)

        submission, _ = MissionSubmission.objects.get_or_create(user=request.user, mission=mission, date=timezone.localdate())
        if submission.approved:
            return Response({'detail': '이미 완료한 미션이에요.'}, status=status.HTTP_400_BAD_REQUEST)

        results, correct = [], 0
        for q in questions:
            chosen = answers.get(str(q.id))
            ok = isinstance(chosen, int) and not isinstance(chosen, bool) and chosen == q.answer - 1
            correct += ok
            results.append({'id': q.id, 'correct': ok, '_q': q})

        total, need = len(questions), needed_to_pass(len(questions))
        passed = correct >= need

        if passed:
            with transaction.atomic():
                user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
                submission = MissionSubmission.objects.select_for_update().get(pk=submission.pk)
                if submission.approved:
                    return Response({'detail': '이미 완료한 미션이에요.'}, status=400)
                submission.approved = True
                submission.save(update_fields=['approved'])
                grant_reward(user, mission)
            request.user.points, request.user.tickets = user.points, user.tickets
            request.user.water_drops, request.user.sunlight = user.water_drops, user.sunlight
            for r in results:
                q = r.pop('_q')
                r['answer'] = q.answer - 1
                r['explanation'] = q.explanation
            return Response({
                'education': learning_card(mission),
                'passed': True, 'correct': correct, 'total': total, 'need': need, 'results': results,
                'detail': f'퀴즈 성공! {correct}/{total} · {reward_text(mission)}',
                'points': request.user.points, 'tickets': request.user.tickets,
                'water_drops': request.user.water_drops, 'sunlight': request.user.sunlight,
            })

        for r in results:
            r.pop('_q')  # 실패했을 땐 어느 문제가 틀렸는지만 알려주고 정답은 숨김
        return Response({
            'passed': False, 'correct': correct, 'total': total, 'need': need, 'results': results,
            'detail': f'{correct}/{total}개 맞혔어요. {need}개 이상 맞혀야 해요. 틀린 문제를 다시 생각해 봐요!',
        })


class WeeklyGoalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def state(self, user):
        from django.db.models import Sum
        from garden.models import WeeklyGoalClaim
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        qs = MissionSubmission.objects.filter(user=user, approved=True, date__gte=monday, date__lt=monday + timedelta(days=7))
        count = qs.count()
        points = qs.aggregate(value=Sum('mission__reward_points'))['value'] or 0
        return {'week_start': str(monday), 'week_end': str(monday + timedelta(days=6)),
                'completed': count, 'required': 7, 'mission_points': points, 'required_points': 150,
                'eligible': count >= 7 and points >= 150,
                'claimed': WeeklyGoalClaim.objects.filter(user=user, week_start=monday).exists(), 'reward': 80}

    def get(self, request):
        return Response(self.state(request.user))

    def post(self, request):
        from datetime import date
        from garden.models import WeeklyGoalClaim
        with transaction.atomic():
            user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
            state = self.state(user)
            if not state['eligible'] or state['claimed']:
                return Response({'detail': '이번 주 목표를 달성한 뒤 한 번만 받을 수 있어요.'}, status=400)
            WeeklyGoalClaim.objects.create(user=user, week_start=date.fromisoformat(state['week_start']))
            user.points += 80
            user.save(update_fields=['points'])
            state['claimed'] = True
        return Response({**state, 'points': user.points, 'detail': '주간 목표 달성! +80P'})
