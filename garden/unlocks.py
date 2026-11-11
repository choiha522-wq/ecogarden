def assign_unlock_levels(SeedType):
    """쉬움 씨앗은 1레벨부터, 보통·어려움은 해당 난이도 레벨부터 열어요.

    보통과 어려움 안에서는 종을 여러 레벨에 나눠 새 선택지를 계속 제공해요.
    """
    SeedType.objects.filter(difficulty=1).update(unlock_level=1)
    for difficulty in (2, 3):
        species = list(SeedType.objects.filter(difficulty=difficulty).order_by('kind', 'id'))
        species.sort(key=lambda item: (item.key != 'pine', item.kind, item.pk))
        total = max(1, len(species))
        for index, plant in enumerate(species):
            level = min(7, difficulty + index * (8 - difficulty) // total)
            SeedType.objects.filter(pk=plant.pk).update(unlock_level=level)
