from datetime import timedelta
from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from garden.models import GardenPlot, GardenProgress, SeedType, UserSeedInventory, PlantCollection
from garden.progression import plot_count_for_level, unlocked_slot_indexes, calculate_level, requirements_for_target_level
from missions.models import Mission, MissionSubmission
from shop.models import ShopItem


class FeedbackIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='test-password', points=500)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.seed = SeedType.objects.create(key='testtree', name='시험나무', emoji='🌳', unlock_level=1)
        self.progress = GardenProgress.objects.create(user=self.user)
        self.plot = GardenPlot.objects.create(user=self.user, slot_index=0, seed_type=self.seed, growth_stage=4)

    def test_tutorial_claim_exactly_once(self):
        self.assertTrue(self.client.post('/api/auth/tutorial/start/').data['show_tutorial'])
        for _ in range(3):
            self.assertFalse(self.client.post('/api/auth/tutorial/start/').data['show_tutorial'])
        other = APIClient()
        other.force_authenticate(User.objects.get(pk=self.user.pk))
        self.assertFalse(other.post('/api/auth/tutorial/start/').data['show_tutorial'])

    def test_tutorial_requires_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post('/api/auth/tutorial/start/').status_code, 401)

    def test_harvest_and_duplicate_prevention(self):
        r = self.client.post('/api/garden/0/harvest/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['points'], 520)
        self.assertEqual(PlantCollection.objects.get(user=self.user, seed_type=self.seed).harvested_count, 1)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.easy_completed, 1)
        self.plot.refresh_from_db()
        self.assertTrue(self.plot.is_empty)
        self.assertEqual(self.client.post('/api/garden/0/harvest/').status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.points, 520)

    def test_legacy_completed_not_counted_again(self):
        self.plot.completion_recorded = True
        self.plot.save()
        self.progress.easy_completed = 3
        self.progress.level = 2
        self.progress.save()
        self.assertEqual(self.client.post('/api/garden/0/harvest/').status_code, 200)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.easy_completed, 3)

    def test_immature_or_dead_cannot_harvest(self):
        for stage, death in [(2, ''), (4, 'water')]:
            self.plot.growth_stage, self.plot.death_reason = stage, death
            self.plot.save()
            self.assertEqual(self.client.post('/api/garden/0/harvest/').status_code, 400)
        self.assertFalse(PlantCollection.objects.exists())

    def test_seven_levels_and_slots(self):
        for level, count in enumerate([9, 11, 13, 16, 19, 22, 25], 1):
            self.assertEqual(plot_count_for_level(level), count)
            self.assertEqual(len(set(unlocked_slot_indexes(5, level))), count)
            req = requirements_for_target_level(level)
            self.progress.easy_completed, self.progress.medium_completed, self.progress.hard_completed = req[1], req[2], req[3]
            self.assertEqual(calculate_level(self.progress), level)
        self.assertEqual(set(unlocked_slot_indexes(5, 7)), set(range(25)))

    def test_themes_charge_once_and_validate(self):
        for theme, expected in [('spring', 500), ('winter', 460), ('spring', 460), ('winter', 460)]:
            r = self.client.post('/api/garden/style/', {'theme': theme}, format='json')
            self.assertEqual(r.status_code, 200, r.data)
            self.assertEqual(r.data['points'], expected)
        self.assertEqual(self.client.post('/api/garden/style/', {'theme': 'invalid'}).status_code, 400)

    def test_theme_insufficient_points(self):
        self.user.points = 0
        self.user.save()
        self.assertEqual(self.client.post('/api/garden/style/', {'theme': 'autumn'}).status_code, 400)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.theme, 'spring')

    def test_catalog_collection_unlock_and_shop_level(self):
        rare = SeedType.objects.create(key='raretest', name='희귀나무', emoji='🌲', description='상세정보', unlock_level=2)
        item = ShopItem.objects.create(item_type='seed', seed_type=rare, name='희귀씨앗', emoji='🌱', price=30)
        def catalog():
            return next(x for x in self.client.get('/api/garden/species/').data if x['key'] == 'raretest')
        self.assertFalse(catalog()['encyclopedia_unlocked'])
        self.assertEqual(catalog()['description'], '')
        self.assertEqual(self.client.post(f'/api/shop/{item.pk}/buy/').status_code, 400)
        self.progress.level = 2
        self.progress.save()
        self.assertEqual(self.client.post(f'/api/shop/{item.pk}/buy/').status_code, 200)
        self.assertTrue(catalog()['encyclopedia_unlocked'])
        self.assertEqual(catalog()['description'], '상세정보')

    def test_preowned_high_level_seeds_still_plantable(self):
        rare = SeedType.objects.create(key='legacyseed', name='기존씨앗', emoji='🌲', unlock_level=7)
        UserSeedInventory.objects.create(user=self.user, seed_type=rare, quantity=1)
        self.client.get('/api/garden/')
        r = self.client.post('/api/garden/1/plant/', {'seed_key': rare.key}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(UserSeedInventory.objects.get(user=self.user, seed_type=rare).quantity, 0)

    def test_legacy_occupied_slot_visible(self):
        GardenPlot.objects.create(user=self.user, slot_index=24, seed_type=self.seed, growth_stage=2)
        data = self.client.get('/api/garden/').data
        self.assertTrue(next(p for p in data['plots'] if p['slot_index'] == 24)['unlocked'])
        self.assertEqual(data['plot_count'], 10)

    def test_weekly_goal_once_and_week_boundary(self):
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        for i in range(7):
            mission = Mission.objects.create(title=f'미션{i}', description='설명', category='observation', reward_points=25)
            MissionSubmission.objects.create(user=self.user, mission=mission, date=today, approved=True)
        old = Mission.objects.create(title='지난주', description='설명', category='observation', reward_points=100)
        MissionSubmission.objects.create(user=self.user, mission=old, date=monday-timedelta(days=1), approved=True)
        data = self.client.get('/api/missions/weekly/').data
        self.assertEqual(data['completed'], 7)
        self.assertEqual(data['mission_points'], 175)
        self.assertTrue(data['eligible'])
        self.assertEqual(self.client.post('/api/missions/weekly/').data['points'], 580)
        self.assertEqual(self.client.post('/api/missions/weekly/').status_code, 400)

    def test_weekly_not_eligible(self):
        self.assertEqual(self.client.post('/api/missions/weekly/').status_code, 400)

    def test_template_and_assets(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'feedback/feedback.')
        self.assertContains(response, 'tutorial/tutorial.')


class LegacyMigrationTests(TransactionTestCase):
    def test_existing_inventory_plants_and_counters_survive(self):
        executor = MigrationExecutor(connection)
        targets = [('garden', '0006_gardenplot_completion_recorded_seedtype_unlock_level_and_more'), ('accounts', '0005_alter_user_id')]
        executor.migrate(targets)
        apps = executor.loader.project_state(targets).apps
        OldUser = apps.get_model('accounts', 'User')
        user = OldUser.objects.create(username='legacy', points=321)
        seed = apps.get_model('garden', 'SeedType').objects.create(key='legacy', name='보존나무', emoji='🌳')
        apps.get_model('garden', 'UserSeedInventory').objects.create(user_id=user.pk, seed_type_id=seed.pk, quantity=4)
        apps.get_model('garden', 'GardenPlot').objects.create(user_id=user.pk, slot_index=24, seed_type_id=seed.pk, growth_stage=4, completion_recorded=True)
        apps.get_model('garden', 'GardenProgress').objects.create(user_id=user.pk, level=3, easy_completed=8, medium_completed=4)
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.points, 321)
        self.assertIsNotNone(user.tutorial_seen_at)
        self.assertEqual(UserSeedInventory.objects.get(user=user).quantity, 4)
        self.assertEqual(GardenPlot.objects.get(user=user, slot_index=24).growth_stage, 4)
        self.assertEqual(GardenProgress.objects.get(user=user).easy_completed, 8)
        self.assertEqual(PlantCollection.objects.get(user=user).harvested_count, 0)
