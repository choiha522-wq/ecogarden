from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction
from rest_framework.views import APIView

from accounts.models import User

from garden.models import GardenProgress, UserSeedInventory, PlantCollection
from .models import ShopItem
from .serializers import ShopItemSerializer


class ShopItemListView(generics.ListAPIView):
    """상점 아이템 목록. 로그인 안 해도 구경할 수 있어요 (구매는 로그인 필요)."""
    queryset = ShopItem.objects.filter(is_available=True).select_related('seed_type')
    serializer_class = ShopItemSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        context['garden_level'] = (GardenProgress.objects.filter(user=user).values_list('level', flat=True).first() or 1) if user.is_authenticated else 1
        return context


class BuyItemView(APIView):
    """포인트로 아이템 구매. index.html의 buy(k,p,t) 함수에 대응."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, item_id):
        item = ShopItem.objects.filter(pk=item_id, is_available=True).first()
        if item is None:
            return Response({'detail': '존재하지 않는 아이템이에요.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if item.seed_type_id:
                progress, _ = GardenProgress.objects.get_or_create(user=user)
                if item.seed_type.unlock_level > progress.level:
                    return Response({'detail': f'{item.seed_type.name} 씨앗은 정원 레벨 {item.seed_type.unlock_level}에서 열려요.'}, status=400)
            if user.points < item.price:
                return Response({'detail': '포인트가 부족해요.'}, status=status.HTTP_400_BAD_REQUEST)

            user.points -= item.price
            if item.item_type == 'seed':
                inv, _ = UserSeedInventory.objects.get_or_create(user=user, seed_type=item.seed_type)
                inv = UserSeedInventory.objects.select_for_update().get(pk=inv.pk)
                PlantCollection.objects.get_or_create(user=user, seed_type=item.seed_type)
                inv.quantity += 1
                inv.save(update_fields=['quantity'])
            elif item.item_type == 'nutrient':
                user.nutrients += 1
            elif item.item_type == 'microbe':
                user.microbes += 1
            elif item.item_type == 'water':
                user.water_drops += item.quantity
            elif item.item_type == 'sunlight':
                user.sunlight += item.quantity
            elif item.item_type == 'ticket':
                user.tickets += 1
            user.save()

        return Response({
            'detail': f'{item.name} 구매 완료!',
            'points': user.points,
            'tickets': user.tickets,
            'nutrients': user.nutrients,
            'microbes': user.microbes,
            'water_drops': user.water_drops,
            'sunlight': user.sunlight,
        })
