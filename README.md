# 초록정원

Django REST Framework로 만든 생태 교육 정원 게임입니다. 로그인 후 미션을 하고, 정원을 가꾸고, 포인트로 아이템을 구매할 수 있습니다.

## 실행 방법

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000/`을 엽니다. 기존 개발 환경에서 업데이트할 때는 가상환경을 활성화한 뒤 `python manage.py migrate`를 실행하세요. 이전 수동 업데이트 스크립트 `apply_update4.py`는 다시 실행하지 마세요.

## 주요 기능

- 출석 보상은 월요일부터 일요일까지 주간 출석 횟수로 계산합니다. 같은 주에 하루를 건너뛰어도 다음 보상 단계로 이어집니다.
- 친구 코드를 등록하고 친구 정원을 볼 수 있습니다. 친구 추가 보상과 응원 보상은 계정 포인트에 저장되며, 응원은 친구별 하루 한 번입니다.
- 포인트는 미션, 출석, 친구 활동, 티켓을 사용한 미니게임에서 적립됩니다. 상점 구매는 같은 계정 잔액을 사용합니다.
- 미션은 사진·퀴즈·관찰 기록 세 유형이며, 하루에 사진 2개·퀴즈 2개·관찰 기록 1개를 우선 뽑습니다.
- 정원 레벨은 제한 없이 성장합니다. 레벨 1→2는 쉬움 식물 3그루, 2→3은 보통 4그루, 3→4는 어려움 5그루를 끝까지 키우며, 이후 난이도를 반복하고 요구 수를 레벨마다 1씩 늘립니다.
- 레벨 2에서 4x4, 레벨 3에서 5x5까지 땅이 열립니다. 종별 도감과 상점은 난이도·레벨 순으로 단계 해제되며, 잠긴 씨앗은 API에서도 구매와 사진 심기를 막습니다.
- 새 가입자는 시작 포인트 30점과 소나무 씨앗 1개를 받아 바로 정원을 시작할 수 있습니다. 씨앗 데이터가 없으면 `seed_demo_data`를 먼저 실행하세요.
- 관찰 기록은 15~500자로 제출하며 자유 문장은 저장하지 않습니다. 선택한 시·도, 장소 유형, 관찰 대상만 저장해 최근 30일 익명 집계에 씁니다. 정확한 위치는 수집하지 않습니다.
- 도감/상점은 자생·외래 여부를 확인하지 못한 종을 '기원 확인 중'으로 표시합니다. 확인된 종에는 학명과 공식 출처 링크를 함께 제공합니다. AI 미션 생성은 출처가 등록된 종 자료만 검색 문맥으로 사용하며, 지역 분포를 추측하지 않도록 제한합니다.
- CO₂와 성장 수치는 게임 시뮬레이션 값이며 실제 대기 측정값이 아닙니다.
- 사진 미션은 실제 이미지 형식과 파일 크기를 확인하고 JPEG로 변환한 뒤 AI로 판정합니다. 무관한 사진은 거절하고, 판정 서비스 장애는 완료 처리하지 않습니다.


## Render에 무료로 배포하기

저장소 루트의 `render.yaml`과 `build.sh`로 Render Blueprint 배포를 구성했습니다. 코드를 GitHub 저장소에 올린 뒤 Render에서 Blueprint를 만들고 저장소를 선택하세요. `GEMINI_API_KEY`는 Render 대시보드의 환경 변수에서 입력해야 하며, `.env`를 업로드하지 마세요.

무료 웹 서비스는 유휴 상태에서 잠들고, 무료 PostgreSQL 데이터베이스는 30일 후 만료됩니다. Render 무료 서비스의 로컬 파일은 재시작 때 보존되지 않으므로 업로드 파일 저장에는 쓰지 않습니다. 장기 운영 전에 데이터베이스와 파일 저장소를 영구 보존 가능한 요금제로 전환하세요.

## 환경 변수

사진 검증과 AI 식물 인식에는 Google Gemini API 키가 필요합니다. [Google AI Studio에서 키를 발급](https://ai.google.dev/gemini-api/docs/api-key)한 뒤 프로젝트 폴더의 `.env` 파일에서 `GEMINI_API_KEY=` 뒤에 키를 입력하세요. `.env`가 없으면 `.env.example`을 복사해 만들 수 있습니다. 기본 모델은 `gemini-3.8-flash`이며, `GEMINI_MODEL`로 바꿀 수 있습니다. 키를 입력한 뒤 Django 서버를 완전히 종료하고 다시 시작해야 적용됩니다. 키는 비밀번호처럼 다루고 채팅이나 저장소에 올리지 마세요.

로컬 개발은 기본으로 `DJANGO_DEBUG=true`와 `localhost,127.0.0.1`을 사용합니다. 배포 전에는 `DJANGO_DEBUG=false`, 임의의 강한 `DJANGO_SECRET_KEY`, 실제 도메인을 쉼표로 구분한 `DJANGO_ALLOWED_HOSTS`를 지정하세요.

## 주요 API

| 기능 | 경로 |
|---|---|
| 내 정보와 잔액 | `GET /api/auth/me/` |
| 주간 출석 보상 | `POST /api/auth/attendance/` |
| 친구 목록·추가 | `GET/POST /api/auth/friends/` |
| 친구 응원 | `POST /api/auth/friends/<id>/cheer/` |
| 게임 티켓 사용 | `POST /api/auth/consume-ticket/` |
| 게임 보상 받기 | `POST /api/auth/mini-game/finish/` |
| 오늘 미션 | `GET /api/missions/` |
| 사진 미션 제출 | `POST /api/missions/<id>/submit/` |
| 관찰 기록 제출 | `POST /api/missions/<id>/record/submit/` |
| 최근 관찰 통계 | `GET /api/missions/observations/summary/` |
| 퀴즈 제출 | `POST /api/missions/<id>/quiz/submit/` |
| 지역 기반 미션 생성 프롬프트 | `python manage.py generate_missions --print-prompt --region 경기` |
| 상점 아이템 구매 | `POST /api/shop/<id>/buy/` |

미션 보상은 완료 여부와 잔액을 한 번의 데이터베이스 작업으로 처리합니다. 포인트를 요청자가 임의로 직접 적립하는 API는 제공하지 않습니다.
