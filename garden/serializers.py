from rest_framework import serializers

from . import sim
from .models import GardenPlot, SeedType, UserSeedInventory


class SeedTypeSerializer(serializers.ModelSerializer):
    """씨앗(나무·꽃) 정보. 프론트가 상점/정원/3D 모양을 그릴 때 이걸 써요."""
    palette = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    difficulty_label = serializers.CharField(source='get_difficulty_display', read_only=True)

    class Meta:
        model = SeedType
        fields = (
            'id', 'key', 'name', 'emoji', 'description', 'price', 'kind', 'difficulty', 'season',
            'water_need', 'sun_need', 'soil_need', 'benefits', 'shape', 'palette', 'accent', 'trunk',
            'width', 'stem_height', 'stem_count', 'center', 'scientific_name', 'origin_status',
            'difficulty_label', 'unlock_level',
            'ecology_notes', 'source_title', 'source_url', 'reference_image_url',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get('catalog'):
            unlocked = instance.unlock_level <= 1 or instance.key in self.context.get('collected_keys', set())
            data['collected'] = instance.key in self.context.get('collected_keys', set())
            data['encyclopedia_unlocked'] = unlocked
            if not unlocked:
                for field in ('description', 'scientific_name', 'ecology_notes', 'source_title', 'source_url', 'reference_image_url', 'benefits'):
                    data[field] = [] if field == 'benefits' else ''
        return data

    def get_palette(self, obj):
        return [c for c in obj.palette.split(',') if c]

    def get_benefits(self, obj):
        return [b for b in obj.benefits.split(',') if b]


class UserSeedInventorySerializer(serializers.ModelSerializer):
    seed_type = SeedTypeSerializer(read_only=True)

    class Meta:
        model = UserSeedInventory
        fields = ('seed_type', 'quantity')


class GardenPlotSerializer(serializers.ModelSerializer):
    """화분 한 칸의 상태. 햇빛은 이웃 나무에 따라 달라지므로 context['sun']으로 받아요."""
    seed_type = SeedTypeSerializer(read_only=True)
    growth_stage_label = serializers.ReadOnlyField()
    is_empty = serializers.ReadOnlyField()
    is_dead = serializers.ReadOnlyField()
    water = serializers.SerializerMethodField()
    nutrients = serializers.SerializerMethodField()
    microbes = serializers.SerializerMethodField()
    sun = serializers.SerializerMethodField()
    sun_ambient = serializers.SerializerMethodField()
    sun_boost = serializers.SerializerMethodField()
    growth_progress = serializers.SerializerMethodField()
    growth_speed = serializers.SerializerMethodField()
    stress_limit = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()

    class Meta:
        model = GardenPlot
        fields = (
            'id', 'slot_index', 'seed_type', 'growth_stage', 'growth_stage_label', 'growth_progress',
            'is_empty', 'is_dead', 'unlocked', 'death_reason', 'stress', 'stress_reason', 'stress_limit',
            'water', 'nutrients', 'microbes', 'sun', 'sun_ambient', 'sun_boost', 'growth_speed', 'photo', 'pixel_photo',
        )

    def _ambient(self, obj):
        return self.context.get('sun', {}).get(obj.slot_index, 100.0)

    def _sun(self, obj):
        return min(100.0, self._ambient(obj) + obj.sun_boost)   # 실제로 받는 햇빛

    def get_water(self, obj): return round(obj.water)
    def get_nutrients(self, obj): return round(obj.nutrients)
    def get_microbes(self, obj): return round(obj.microbes)
    def get_sun(self, obj): return round(self._sun(obj))
    def get_sun_ambient(self, obj): return round(self._ambient(obj))
    def get_sun_boost(self, obj): return round(obj.sun_boost)
    def get_growth_progress(self, obj): return round(obj.growth_progress, 2)
    def get_growth_speed(self, obj): return sim.growth_speed(obj, self._sun(obj), self.context.get('poll', 1.0))
    def get_stress_limit(self, obj): return sim.STRESS_LIMIT
    def get_unlocked(self, obj): return obj.slot_index in self.context.get('unlocked_slot_indexes', set())
