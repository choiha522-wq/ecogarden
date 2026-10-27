"""
사진 속 식물이 어떤 종인지 AI(Gemini)로 알아보는 기능.

우리 게임에 있는 식물 목록(나무·꽃 41종) 중에서 "같은 종" 또는 "가장 비슷한 종"을 골라요.
(목록에 없는 식물이면 가장 비슷한 종으로 심고, 식물이 아니면 거절해요.)
"""
import json

from django.conf import settings

from missions.services import _generate

from .models import SeedType


class AIUnavailable(Exception):
    """GEMINI_API_KEY가 없어서 AI를 쓸 수 없을 때."""


def identify_plant(image_bytes):
    """
    image_bytes: JPEG로 줄인 사진 데이터
    반환: {'is_plant': bool, 'species_key': str|None, 'match': 'exact'|'similar'|'none', 'label': str, 'reason': str}
    """
    if not settings.GEMINI_API_KEY:
        raise AIUnavailable()

    from google.genai import types

    catalog = '\n'.join(
        f"- {s.key}: {s.name} ({'나무' if s.kind == 'tree' else '꽃'})"
        for s in SeedType.objects.order_by('kind', 'id')
    )
    prompt = f"""너는 어린이용 생태 교육 게임의 식물 판별 AI야.
사진 속 식물이 아래 [목록] 중 어떤 종인지 골라줘.

[목록]
{catalog}

[규칙]
- species_key에는 반드시 [목록]에 있는 key만 써. 목록에 없는 이름을 만들지 마.
- 사진에 나무, 꽃, 풀 같은 식물이 뚜렷하게 있으면 is_plant를 true로 해.
- 목록의 종과 정확히 같으면 match를 "exact", 목록에서 가장 비슷한 종을 골랐으면 "similar"로 해.
- 식물이 없거나 사람, 동물, 음식, 물건, 화면 캡처뿐이면 is_plant를 false, species_key를 null, match를 "none"으로 해.
- label에는 사진 속 식물의 실제 이름을 한글로 써 (모르면 "알 수 없는 식물"). 사람이나 개인정보는 언급하지 마.
- reason은 어린이가 이해할 쉬운 말 한 문장으로 써.

아래 JSON 형식으로만 답해.
{{"is_plant": true, "species_key": "oak", "match": "exact", "label": "참나무", "reason": "잎이 넓고 가장자리가 물결 모양이라 참나무 같아요."}}"""

    resp = _generate([types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), prompt])
    text = (resp.text or '').strip().strip('`')
    if text.lower().startswith('json'):
        text = text[4:].strip()
    data = json.loads(text)
    return {
        'is_plant': bool(data.get('is_plant')),
        'species_key': data.get('species_key') or None,
        'match': str(data.get('match', 'none')),
        'label': str(data.get('label', ''))[:40],
        'reason': str(data.get('reason', ''))[:200],
    }
