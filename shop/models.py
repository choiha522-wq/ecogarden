from django.db import models

from garden.models import SeedType


class ShopItem(models.Model):
    """
    index.html의 shop() 함수(it 배열)를 DB 모델로 옮긴 것.
    item_type이 'seed'면 seed_type을 지정, 'nutrient'/'ticket'이면 seed_type은 비워둠.
    """
    ITEM_TYPE_CHOICES = [
        ('seed', '씨앗'),
        ('nutrient', '영양제'),
        ('microbe', '미생물제'),
        ('water', '물방울'),
        ('sunlight', '햇빛 조각'),
        ('ticket', '게임 티켓'),
    ]

    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    seed_type = models.ForeignKey(SeedType, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=8)
    description = models.CharField(max_length=200, blank=True)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)  # 한 번 사면 몇 개를 받는지 (예: 물방울 5개 묶음)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
