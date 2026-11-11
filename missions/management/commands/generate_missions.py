"""
AI(Gemini)로 새 생태 미션(사진 인증형 / 퀴즈형)을 자동 생성해서 DB에 저장하는 커맨드.

사용법:
    python manage.py generate_missions                 # 기본 5개 생성 (비공개 상태로 저장)
    python manage.py generate_missions --count 10
    python manage.py generate_missions --season 가을 --grade "초등 저학년"
    python manage.py generate_missions --dry-run       # DB에 저장하지 않고 결과만 출력
    python manage.py generate_missions --publish       # 검토 없이 바로 공개 (비추천)
    python manage.py generate_missions --print-prompt  # 프롬프트만 출력 (Gemini 웹 등에 붙여넣기용)

학생에게 보이는 콘텐츠라서, 기본값은 "비공개(is_active=False)"로 저장합니다.
/admin/ 에서 내용(특히 퀴즈 정답·해설)을 확인한 뒤 '공개' 체크를 켜세요.
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from missions.models import Mission, QuizQuestion

CATEGORY_GUIDE = """- observation(관찰): 야외에서 식물·곤충·흙·날씨 등을 직접 보고 기록하는 미션
- microbe(미생물): 낙엽 분해, 흙 속 생물, 발효 등 눈에 안 보이는 생태계를 배우는 미션
- biology(생물): 식물·곤충·새 등 생물의 특징, 생태계 안의 관계, 생물다양성을 알아보는 미션"""

PROMPT_TEMPLATE = """너는 초·중·고등학생을 위한 '육상생태계' 교육 서비스 「초록정원」의 미션 기획자야.
학생들은 미션을 수행하면 포인트를 받아 씨앗·영양제로 바꾸고, 나만의 생태정원을 가꾸며 생태계를 배워.

[이번에 만들 미션]
- 개수: {count}개
- 대상 학년: {grade}
- 계절/시기: {season}
- 관찰 지역(시·도 단위): {region}
- 지역 정보가 제공되어도, 아래 출처 자료에 해당 지역 분포가 없으면 그 지역에 특정 종이 산다고 단정하지 마.

[미션 종류] mission_type
- record: 사진 없이 짧은 관찰 기록(무엇을 봤는지, 어떤 점이 궁금했는지)을 작성하는 미션. description에 기록 방법을 안내해.
- photo: 학생이 사진을 찍어 인증하는 미션. AI가 사진만 보고 판정할 수 있는 구체적 대상(예: "민들레 찾기", "곤충 1마리", "낙엽 3종류")이어야 해.
- quiz: 퀴즈를 풀어 맞히는 미션. 반드시 questions(문제 3개)를 포함해.
photo, quiz, record를 섞어서 만들어. 사진 인증은 전체의 20% 이하로 구성하고, 관찰 기록과 퀴즈를 충분히 섞어.

[공식 출처 기반 종 자료]
{species_context}
각 종의 이름·생태 설명은 위에서 확인 가능한 범위만 사용하고, 외래/자생을 추측하지 마. 지역별 분포가 목록에 없으면 흔한 장소 유형(학교 화단·공원)에서 누구나 관찰할 수 있는 기록형 과제로 구성해.

[카테고리 설명]
{category_guide}

[공통 작성 규칙]
1. 학생이 혼자 또는 보호자·선생님과 안전하게 할 수 있는 활동만 만들어. 위험한 곳(도로변·차도 근처, 물가, 높은 곳)이나 야생동물 접촉, 식물 채취·훼손을 유도하면 안 돼. "길가" 같은 도로를 연상시키는 장소 표현도 쓰지 마. 곤충·동물은 "만지지 말고 멀리서 관찰"하도록 안내해.
2. 학교·집 근처 공원, 화단, 베란다, 운동장처럼 누구나 접근 가능한 장소에서 가능해야 해.
3. title은 20자 이내의 쉬운 말, description은 1~2문장으로 "무엇을 하면 되는지"를 구체적으로 써. 학년에 맞는 어휘를 써.
4. reward_points는 쉬움 30, 보통 40, 어려움 50~60. reward_tickets는 모두 1.
5. 카테고리가 골고루 섞이게 하고, 아래 [이미 있는 미션]과 겹치거나 비슷한 것은 만들지 마.
6. emoji는 미션을 대표하는 이모지 1개.

[photo 전용 규칙]
- ai_assisted는 AI가 사진 속 식물·곤충 등을 인식해서 검증해야 하면 true, 아니면 false.
- 퀴즈·문제 풀이 같은 표현은 쓰지 마.

[record 전용 규칙]
- ai_assisted는 false로 하고, questions는 만들지 마.
- 학생이 사진을 올리거나 정답을 맞힐 필요 없이 1~2문장으로 직접 관찰을 기록하도록 해.

[quiz 전용 규칙]
- ai_assisted는 항상 false.
- questions는 정확히 3개. 각 문제는 text(문제), choices(보기 3~4개), answer_index(정답 보기의 번호, 0부터 시작), explanation(해설 1~2문장)을 가져.
- 사실로 확인된 과학적 내용만 써. 확실하지 않은 내용, 논란이 있는 내용은 쓰지 마. 정답은 단 하나여야 하고, 오답 보기는 틀린 게 분명해야 해.
- 정답 위치가 한쪽에 몰리지 않게 answer_index를 골고루 섞어.
- 문제와 해설은 학년에 맞는 쉬운 말로 써.

[이미 있는 미션]
{existing}

[출력 형식]
설명이나 코드블록 없이, 아래 구조의 JSON 배열만 출력해. quiz가 아닌 미션은 questions를 생략해.
[
  {{
    "title": "...",
    "description": "...",
    "category": "observation | microbe | biology 중 하나",
    "mission_type": "photo | quiz | record 중 하나",
    "emoji": "🌱",
    "reward_points": 30,
    "reward_tickets": 1,
    "ai_assisted": true,
    "questions": [
      {{"text": "...", "choices": ["...", "...", "..."], "answer_index": 0, "explanation": "..."}}
    ]
  }}
]"""

VALID_CATEGORIES = {'observation', 'microbe', 'biology'}
VALID_TYPES = {'photo', 'quiz', 'record'}


def build_prompt(count, grade, season, region='대한민국(지역 미지정)'):
    from garden.models import SeedType
    sourced = SeedType.objects.exclude(source_url='').exclude(origin_status='unverified').order_by('name')
    species_context = '\n'.join(
        f"- {sp.name} ({sp.scientific_name or '학명 확인 중'}): {sp.ecology_notes or sp.description} [출처: {sp.source_title} {sp.source_url}]"
        for sp in sourced
    ) or '- 현재 검증된 종 자료가 없으므로 특정 종의 자생·외래 여부나 지역 분포를 단정하지 말 것.'
    existing = '\n'.join(f'- {t}' for t in Mission.objects.values_list('title', flat=True)) or '(없음)'
    return PROMPT_TEMPLATE.format(
        count=count, grade=grade, season=season,
        category_guide=CATEGORY_GUIDE, existing=existing, region=region, species_context=species_context,
    )


def _clean_question(q):
    """문제 1개를 검증해서 모델 필드 dict로 반환. 이상하면 None."""
    try:
        choices = [str(c).strip()[:100] for c in q['choices'] if str(c).strip()][:4]
        idx = q['answer_index']
        if not isinstance(idx, int) or isinstance(idx, bool):
            return None
        text = str(q['text']).strip()
        if not text or len(choices) < 2 or not 0 <= idx < len(choices):
            return None
    except (KeyError, TypeError):
        return None
    c = choices + [''] * (4 - len(choices))
    return {
        'text': text[:200], 'choice1': c[0], 'choice2': c[1], 'choice3': c[2], 'choice4': c[3],
        'answer': idx + 1, 'explanation': str(q.get('explanation', ''))[:300],
    }


def parse_missions(text):
    """모델 응답에서 JSON 배열을 안전하게 꺼내 검증된 dict 리스트로 반환. (quiz는 'questions' 키 포함)"""
    text = text.strip()
    start, end = text.find('['), text.rfind(']')
    if start == -1 or end == -1:
        raise ValueError('JSON 배열을 찾지 못했어요.')
    items = json.loads(text[start:end + 1])

    cleaned = []
    for it in items:
        if it.get('category') not in VALID_CATEGORIES or not it.get('title') or not it.get('description'):
            continue
        mtype = it.get('mission_type', 'photo')
        if mtype not in VALID_TYPES:
            continue

        mission = {
            'title': str(it['title'])[:100],
            'description': str(it['description']),
            'category': it['category'],
            'mission_type': mtype,
            'emoji': str(it.get('emoji', '🌱'))[:8],
            'reward_points': max(30, min(int(it.get('reward_points', 40)), 60)),
            'reward_tickets': max(0, min(int(it.get('reward_tickets', 1)), 3)),
            'reward_water': 1 if mtype == 'photo' else 2,
            'reward_sunlight': 1 if mtype == 'photo' else 0,
            'requires_photo': mtype == 'photo',
            'ai_assisted': bool(it.get('ai_assisted', False)) and mtype == 'photo',
        }
        if mtype == 'record':
            mission['ai_assisted'] = False
            mission['requires_photo'] = False
        if mtype == 'quiz':
            qs = [x for x in (_clean_question(q) for q in it.get('questions', [])) if x]
            if len(qs) < 2:  # 쓸 만한 문제가 2개 미만이면 퀴즈 미션 자체를 버림
                continue
            mission['questions'] = qs
        cleaned.append(mission)
    return cleaned


class Command(BaseCommand):
    help = 'Gemini로 새 생태 미션(사진 인증/퀴즈)을 자동 생성해서 DB에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5)
        parser.add_argument('--grade', default='초등 고학년~중학생')
        parser.add_argument('--season', default='계절 무관')
        parser.add_argument('--region', default='대한민국(지역 미지정)', help='관찰 지역(시·도 단위, 예: 경기)')
        parser.add_argument('--dry-run', action='store_true', help='DB에 저장하지 않고 결과만 출력')
        parser.add_argument('--publish', action='store_true', help='검토 없이 바로 공개 상태로 저장')
        parser.add_argument('--print-prompt', action='store_true', help='프롬프트만 출력하고 종료')

    def handle(self, *args, **opts):
        prompt = build_prompt(opts['count'], opts['grade'], opts['season'], opts['region'])

        if opts['print_prompt']:
            self.stdout.write(prompt)
            return

        if not settings.GEMINI_API_KEY:
            raise CommandError('GEMINI_API_KEY가 설정되지 않았어요. (--print-prompt로 프롬프트만 뽑아 쓸 수도 있어요)')

        from missions.services import generate_text
        try:
            text = generate_text(prompt)
        except Exception as e:
            raise CommandError(f'Gemini 호출에 실패했어요. 잠시 후 다시 시도해 주세요. ({e})')

        try:
            missions = parse_missions(text)
        except (ValueError, json.JSONDecodeError) as e:
            raise CommandError(f'AI 응답을 해석하지 못했어요: {e}\n--- 원문 ---\n{text}')

        if not missions:
            raise CommandError('유효한 미션이 하나도 없었어요. 다시 실행해 주세요.')

        existing = set(Mission.objects.values_list('title', flat=True))
        created = 0
        for m in missions:
            questions = m.pop('questions', [])
            kind = {'quiz': '퀴즈', 'record': '기록'}.get(m['mission_type'], '사진')
            extra = f' · 문제 {len(questions)}개' if questions else ''
            tag = '[미리보기]' if opts['dry_run'] else ('[건너뜀: 중복]' if m['title'] in existing else '[생성]')
            self.stdout.write(f"{tag} {m['emoji']} [{kind}] {m['title']} ({m['category']}, {m['reward_points']}P{extra}) - {m['description']}")
            for i, q in enumerate(questions, 1):
                shown = [q['choice1'], q['choice2'], q['choice3'], q['choice4']]
                self.stdout.write(f"      Q{i}. {q['text']}  (정답: {shown[q['answer'] - 1]})")
            if opts['dry_run'] or m['title'] in existing:
                continue

            with transaction.atomic():
                mission = Mission.objects.create(is_active=opts['publish'], **m)
                for i, q in enumerate(questions):
                    QuizQuestion.objects.create(mission=mission, order=i, **q)
            created += 1

        state = '공개' if opts['publish'] else '비공개(/admin/에서 검토 후 공개해 주세요)'
        self.stdout.write(self.style.SUCCESS(f'완료: {created}개 생성 · {state}'))
