from rest_framework import serializers

from .models import ShopItem


class ShopItemSerializer(serializers.ModelSerializer):
    seed_key = serializers.SerializerMethodField()  # 씨앗이면 어떤 종인지 (종 정보는 /api/garden/species/)
    seed_unlock_level = serializers.SerializerMethodField()
    seed_difficulty = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()

    class Meta:
        model = ShopItem
        fields = ('id', 'item_type', 'name', 'emoji', 'description', 'price', 'quantity', 'seed_key', 'seed_unlock_level', 'seed_difficulty', 'unlocked')

    def get_seed_key(self, obj):
        return obj.seed_type.key if obj.seed_type_id else None

    def get_seed_unlock_level(self, obj):
        return obj.seed_type.unlock_level if obj.seed_type_id else None

    def get_seed_difficulty(self, obj):
        return obj.seed_type.difficulty if obj.seed_type_id else None

    def get_unlocked(self, obj):
        return not obj.seed_type_id or obj.seed_type.unlock_level <= self.context.get('garden_level', 1)
