"""
씨앗(나무·꽃) 종류 데이터. 「생태계에 도움이 되는 나무 20가지 / 꽃 20가지」 이미지를 바탕으로 만들었어요.

- 이름, 난이도(★), 설명, 꽃 피는 계절은 이미지에 적힌 그대로예요.
- water/sun/soil(물·햇빛·흙이 필요한 정도, 1~5)은 이미지의 게이지를 보고 정한 근사값이에요.
  정확하지 않을 수 있으니 이 파일에서 마음대로 고치면 돼요. (고친 뒤 `python manage.py seed_demo_data` 다시 실행)
- 색(palette, accent 등)은 3D 정원에서 어떤 모양으로 보일지를 정하는 값이에요.
- 새 종을 추가하려면 아래 목록에 한 줄 추가하고 seed_demo_data를 실행하세요 (Admin에서도 추가할 수 있어요).
"""


def tree(key, name, emoji, diff, water, sun, soil, shape, palette, desc, benefits='',
         accent='', trunk='8B5A2B', width=1.0, price=None, scientific_name='', origin_status='unverified',
         ecology_notes='', source_title='', source_url='', reference_image_url=''):
    return dict(
        key=key, name=name, emoji=emoji, kind='tree', difficulty=min(diff, 3), season='',
        water_need=water, sun_need=sun, soil_need=soil, shape=shape, palette=palette,
        description=desc, benefits=benefits, accent=accent, trunk=trunk, width=width,
        price=price if price is not None else 25 + 15 * diff,
        scientific_name=scientific_name, origin_status=origin_status, ecology_notes=ecology_notes,
        source_title=source_title, source_url=source_url, reference_image_url=reference_image_url,
    )


def flower(key, name, emoji, diff, season, water, sun, soil, accent, desc,
           center='FFC107', height=1.0, count=3, price=None, scientific_name='', origin_status='unverified',
           ecology_notes='', source_title='', source_url='', reference_image_url=''):
    return dict(
        key=key, name=name, emoji=emoji, kind='flower', difficulty=min(diff, 3), season=season,
        water_need=water, sun_need=sun, soil_need=soil, shape='round',
        palette='3E9B4F,4FB068,6CD07E', description=desc, benefits='벌,나비,새,토양보존',
        accent=accent, center=center, stem_height=height, stem_count=count,
        price=price if price is not None else 5 + 10 * diff,
        scientific_name=scientific_name, origin_status=origin_status, ecology_notes=ecology_notes,
        source_title=source_title, source_url=source_url, reference_image_url=reference_image_url,
    )


SPECIES = [
    # ---------------- 나무 (기존 5종은 가격을 그대로 유지) ----------------
    tree('apple', '사과나무', '🍎', 1, 3, 5, 3, 'round', '2E9E52,3FB765,5CD07A',
         '빨간 열매가 열려요. 새와 곤충이 좋아해요.', '새,곤충', accent='E8443A', price=30),
    tree('pine', '소나무', '🌲', 1, 2, 5, 2, 'conifer', '1F6B3A,2A8548,3A9E5A',
         '새와 곤충의 서식처를 제공하고, 토양을 지켜줘요.', '서식지,토양보호', price=40,
         scientific_name='Pinus densiflora'),
    tree('cherry', '벚나무', '🌸', 1, 3, 5, 3, 'round', 'FF8FB1,FFB6CB,FFD3E0',
         '꿀벌 등 곤충의 먹이가 되고, 다양한 생물의 서식지를 만들어요.', '곤충먹이,서식지',
         trunk='6B4A3A', width=1.25, price=60),
    tree('maple', '단풍나무', '🍁', 1, 3, 4, 3, 'round', 'C93A26,EF7A2A,F2A93B',
         '새들의 먹이가 되고, 숲의 다양성을 높여줘요.', '새먹이,다양성', price=50),
    tree('ginkgo', '은행나무', '🍂', 1, 3, 5, 3, 'tall', 'E0A800,F5D442,FFE680',
         '다양한 곤충과 새들에게 먹이를 제공하고, 도심의 공기 정화에 도움을 줘요.', '곤충먹이,공기정화',
         width=0.8, price=50),
    tree('zelkova', '느티나무', '🌳', 2, 3, 4, 3, 'round', '2E8B3E,48A850,6CC070',
         '새와 곤충의 서식처가 되고, 미세먼지를 흡수해요.', '서식지,미세먼지', width=1.3),
    tree('oak', '참나무', '🌰', 2, 3, 4, 3, 'round', '3D7A2F,4F9440,6AAE55',
         '다람쥐, 새 등 야생동물의 먹이가 되며, 숲의 생물 다양성을 높여요.', '동물먹이,다양성', width=1.2),
    tree('korean_pine', '잣나무', '🌲', 2, 3, 4, 3, 'conifer', '2B6E4A,3A8A5E,55A878',
         '새와 다람쥐의 먹이가 되고, 산림 생태계를 안정시켜요.', '동물먹이,산림안정'),
    tree('birch', '자작나무', '🌳', 2, 2, 5, 2, 'tall', '7FC46A,98D67F,B5E69C',
         '척박한 토양을 개선하며, 다양한 곤충의 서식처가 돼요.', '토양개선,서식지', trunk='EDE8DC', width=0.8),
    tree('chestnut', '밤나무', '🌰', 2, 3, 5, 3, 'round', '4C8C2B,63A83A,7FC04E',
         '새와 동물의 먹이가 되며, 토양을 비옥하게 해요.', '동물먹이,토양비옥', accent='A0522D'),
    tree('persimmon', '감나무', '🍊', 2, 3, 5, 3, 'round', '3E8E41,58A854,74C06D',
         '새와 곤충이 좋아하는 열매를 제공해 생태계의 먹이사슬을 유지해요.', '먹이사슬', accent='FF8A1F'),
    tree('hinoki', '편백나무', '🌲', 3, 4, 3, 3, 'conifer', '2E7D4F,3F9463,5BAF7E',
         '산림의 수분을 보존하고, 피톤치드로 주변 생물에 좋은 환경을 만들어요.', '수분보존,피톤치드'),
    tree('fir', '전나무', '🎄', 3, 4, 3, 3, 'conifer', '1D5C3A,26744A,328E5D',
         '새와 곤충의 서식처가 되고, 산림 생태계를 풍부하게 해요.', '서식지,산림'),
    tree('willow', '버드나무', '🌿', 3, 5, 4, 3, 'willow', '7DBE4A,9AD264,B8E67E',
         '물가의 생태계를 유지하고, 다양한 수서생물에게 그늘과 서식지를 제공해요.', '물가생태계,서식지', width=1.1),
    tree('ash', '물푸레나무', '🌳', 3, 3, 4, 3, 'round', '3F8F3A,58A850,72C167',
         '토양을 안정시키고, 새와 곤충의 먹이가 돼요.', '토양안정,먹이', width=1.1),
    tree('paulownia', '오동나무', '💜', 3, 3, 5, 3, 'round', '3E9B4F,58B466,7ECC84',
         '벌과 나비의 먹이가 되고, 빠르게 자라 숲의 복원에 도움을 줘요.', '곤충먹이,숲복원', accent='9B7FD1'),
    tree('sophora', '회화나무', '🌼', 4, 2, 5, 3, 'round', '3F9B5A,5AB474,7ACE90',
         '꿀벌의 먹이가 되고, 토양 개선과 질소 고정에 도움을 줘요.', '꿀벌먹이,질소고정', accent='FFF3C0'),
    tree('fringe_tree', '이팝나무', '🤍', 4, 3, 4, 3, 'round', 'F2F7EC,FFFFFF,E3EEDD',
         '벌과 나비 등 곤충의 먹이가 되며, 도심의 공기 정화에 효과적이에요.', '곤충먹이,공기정화', width=1.15),
    tree('rowan', '마가목', '🍒', 4, 3, 4, 3, 'round', '3A8A3A,52A252,6EBB6E',
         '새들의 먹이가 되고, 산림 생태계의 다양성을 높여줘요.', '새먹이,다양성', accent='D62828'),
    tree('dogwood', '층층나무', '🌳', 4, 4, 4, 3, 'round', '4A9A4A,64B264,80CB80',
         '새와 곤충의 서식처가 되고, 숲의 구조를 안정시켜요.', '서식지,숲구조', width=1.15),
    tree('bakdal', '박달나무', '🌳', 4, 3, 4, 4, 'round', '2F7A3A,45934F,61AE6B',
         '다양한 곤충과 새의 서식처가 되고, 건강한 숲을 유지하는 데 도움을 줘요.', '서식지,건강한숲',
         trunk='6B5B4B', width=1.1),

    # ---------------- 꽃 ----------------
    flower('forsythia', '개나리', '🌼', 2, '봄', 2, 5, 2, 'FFD93D', '봄에 가장 먼저 피는 꽃으로, 벌과 나비의 먹이가 되어줘요.', 'FFC107', 1.0, 5,
           scientific_name='Forsythia koreana', origin_status='cultivated',
           ecology_notes='한국 특산 식물이지만 현재 자생지가 발견되지 않아 정원에서 재배되는 종으로 안내해요.',
           source_title='국립생물자원관 한반도의 생물다양성',
           source_url='https://species.nibr.go.kr/usef/species/SpeciesTabDetail.do?cmd=t2&currentPage=1&pageIndex=1&specSeq=120000063193&surveyId=NIBR201708614D'),
    flower('cherry_blossom', '벚꽃', '🌸', 2, '봄', 3, 5, 3, 'FFB6CB', '꽃이 피는 시기에 많은 곤충이 찾아오고, 꿀을 제공해요.', 'FFE08A', 1.0, 4),
    flower('tulip', '튤립', '🌷', 2, '봄', 3, 4, 3, 'E8445A', '다양한 곤충을 유인하며, 도시 생태계에도 도움을 줘요.', 'E8445A', 1.0, 3),
    flower('sunflower', '해바라기', '🌻', 2, '여름', 3, 5, 3, 'FFC107', '벌과 나비를 끌어들이고, 씨앗은 새들의 먹이가 돼요.', '6B4A2B', 1.8, 1),
    flower('hydrangea', '수국', '💠', 3, '여름', 4, 3, 4, '8FA8E8', '나비와 벌이 좋아하는 꽃으로, 다양한 곤충의 서식지를 제공해요.', 'B8C8F4', 0.9, 3),
    flower('lavender', '라벤더', '🪻', 2, '여름', 2, 5, 2, '9B7FD1', '벌과 나비를 유인하고, 향으로 해충을 막아줘요.', 'B7A0E8', 1.2, 5),
    flower('lotus', '연꽃', '🪷', 3, '여름', 5, 5, 3, 'F7A8C8', '물속 생태계를 건강하게 하고, 곤충과 수생생물의 서식처가 돼요.', 'FFD54F', 0.6, 2),
    flower('morning_glory', '나팔꽃', '🌀', 2, '여름', 3, 5, 2, '5C6BC0', '나비와 벌이 좋아하며, 덩굴식물로 작은 생물들의 쉼터가 돼요.', 'FFFFFF', 1.1, 3),
    flower('cosmos', '코스모스', '🌺', 2, '가을', 2, 5, 2, 'FF7AA8', '벌과 나비를 끌어들이고, 씨앗은 새들의 먹이가 돼요.', 'FFC107', 1.4, 3),
    flower('chrysanthemum', '국화', '🏵️', 2, '가을', 3, 4, 3, 'FFC107', '늦가을까지 꽃이 피어 곤충에게 지속적인 먹이를 제공해요.', 'FF9800', 0.9, 3),
    flower('gujeolcho', '구절초', '🌼', 2, '가을', 2, 4, 2, 'FFFFFF', '가을철 벌과 나비의 먹이가 되며, 토양을 건강하게 해줘요.', 'FFD54F', 1.0, 4),
    flower('cockscomb', '맨드라미', '🔴', 2, '가을', 3, 5, 3, 'D62839', '벌과 나비를 유인하고, 토양의 영양분을 보존해요.', 'D62839', 1.0, 3),
    flower('marigold', '금잔화', '🟠', 2, '사계절', 3, 5, 2, 'FF9800', '해충을 줄이고, 벌과 나비를 유인해 생태계 균형에 도움을 줘요.', 'FFC107', 0.8, 4),
    flower('camellia', '동백꽃', '🌺', 2, '겨울', 3, 3, 4, 'D62839', '겨울철에도 꽃을 피워 벌과 새에게 먹이를 제공해요.', 'FFD54F', 1.0, 2),
    flower('pansy', '팬지', '🪻', 2, '겨울', 3, 3, 3, '7E57C2', '추운 계절에도 꽃을 피워 곤충의 먹이원이 되어줘요.', 'FFD54F', 0.5, 4),
    flower('dandelion', '민들레', '🌼', 2, '봄', 2, 5, 2, 'FFD93D', '꿀이 풍부해 벌과 나비를 유인하고, 씨앗은 새들의 먹이가 돼요.', 'FFC107', 0.7, 3),
    flower('chickweed', '벼룩이자리', '💠', 2, '봄', 3, 3, 3, '90B4F0', '초기 봄에 피어 곤충의 먹이가 되며, 토양을 비옥하게 해줘요.', 'FFFFFF', 0.5, 5),
    flower('peony', '작약', '🌺', 3, '봄', 3, 4, 4, 'F06292', '다양한 곤충을 유인하고, 꽃가루를 통해 생물다양성에 기여해요.', 'FFD54F', 1.0, 2),
    flower('trumpet_vine', '능소화', '🧡', 2, '여름', 3, 5, 3, 'FF7043', '벌과 나비를 유인하고, 덩굴식물로 새들에게도 쉼터가 돼요.', 'FFC107', 1.4, 3),
    flower('geranium', '쥐손이풀', '💜', 2, '여름', 3, 3, 3, 'B39DDB', '벌과 나비를 유인하고, 토양을 보존해요.', 'FFD54F', 0.7, 4),
]
