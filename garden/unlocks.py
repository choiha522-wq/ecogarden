def assign_unlock_levels(SeedType):
    """각 난이도는 그 난이도가 처음 필요한 레벨부터 구매할 수 있게 배치."""
    for difficulty in (1, 2, 3):
        species = list(SeedType.objects.filter(difficulty=difficulty).order_by('kind', 'id'))
        species.sort(key=lambda item: (item.key != 'pine', item.kind, item.pk))
        total = max(1, len(species))
        for index, plant in enumerate(species):
            level = min(7, difficulty + index * (8 - difficulty) // total)
            SeedType.objects.filter(pk=plant.pk).update(unlock_level=level)
