"""
Gemini(Google AI Studio)를 이용한 AI 기능 모음.
  - verify_mission_photo(): 미션 인증 사진을 보고 통과/거절 판정
  - generate_text():        프롬프트를 보내고 JSON 텍스트를 받는 공용 함수 (미션 자동 생성에 사용)

AI 검증을 수행할 수 없으면 예외를 발생시켜 미션을 통과시키지 않습니다.
"""
import json
import time

from django.conf import settings

def _client():
    from google import genai
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _json_config():
    from google.genai import types
    return types.GenerateContentConfig(response_mime_type='application/json')


# 선택한 모델이 "수요 폭주(503)" 등으로 일시적으로 실패하면 잠깐 기다렸다 재시도하고,
# 그래도 안 되면 아래 예비 모델로 넘어갑니다.
FALLBACK_MODELS = ['gemini-3.6-flash', 'gemini-3.5-flash-lite', 'gemini-2.5-flash']
RETRYABLE = (429, 500, 503, 504)


def _generate(contents):
    client = _client()  # 변수에 담아 둬야 요청 도중 클라이언트가 닫히지 않아요
    models = [settings.GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != settings.GEMINI_MODEL]
    last = None
    for model in models:
        for attempt in range(2):
            try:
                return client.models.generate_content(model=model, contents=contents, config=_json_config())
            except Exception as e:
                last = e
                code = getattr(e, 'code', None)
                if code in RETRYABLE and attempt == 0:
                    time.sleep(2)
                    continue
                # 환경 변수의 모델명이 폐기되었거나 권한이 없으면 예비 모델도 시도해요.
                break
    raise last


def generate_text(prompt):
    """프롬프트를 Gemini에 보내고 응답 텍스트(JSON)를 반환."""
    return _generate(prompt).text or ''


def verify_mission_photo(image_bytes, mission):
    """
    image_bytes: 업로드 원본에서 정규화한 JPEG 바이트
    mission: Mission 인스턴스
    반환: (approved: bool, ai_label: str, message: str)
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError('GEMINI_API_KEY is not configured')

    from google.genai import types

    prompt = f"""너는 어린이를 위한 생태 관찰 미션의 사진 확인자야.
사진에 실제로 보이는 내용과 미션을 비교해.
미션 제목: {mission.title}
미션 설명: {mission.description}

판정 기준:
- 미션 대상이 사진에 분명히 보이거나, 설명한 관찰 활동과 직접 관련되면 approved=true.
- 예를 들어 나비 사진은 나비를 찾거나 꽃가루받이를 관찰하는 미션에 맞아.
- 대상이 전혀 보이지 않거나 셀카, 음식, 실내 물건, 화면 캡처처럼 미션과 무관하면 approved=false.
- 사진이 흐리거나 판단이 어렵다면 이유를 설명하고 approved=false로 해.

반드시 다음 JSON 형식만 출력해:
{{"approved": true, "label": "사진의 핵심 대상", "reason": "쉬운 한국어 한 문장"}}
label과 reason은 어린이가 이해할 쉬운 한국어로 작성해."""

    resp = _generate([types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), prompt])
    text = (resp.text or '').strip()
    if text.startswith('```'):
        text = text.strip('`').strip()
        if text.lower().startswith('json'):
            text = text[4:].strip()

    try:
        data = json.loads(text)
        if not isinstance(data, dict) or not isinstance(data.get('approved'), bool):
            raise RuntimeError('AI returned an invalid photo-verification response')
        return data['approved'], str(data.get('label', ''))[:100], str(data.get('reason', ''))
    except (json.JSONDecodeError, AttributeError) as exc:
        raise RuntimeError('AI returned an unreadable photo-verification response') from exc