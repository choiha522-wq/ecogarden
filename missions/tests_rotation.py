from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from .models import Mission, QuizQuestion, QuizHistory, QuizDraw
from .quiz_rotation import selected_questions

class RotationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='rotation', password='password')
        # 격리된 문제은행을 사용한다.
        self.mission = Mission.objects.create(title='Rotation', category='testrotation', mission_type='quiz')
        for i in range(7):
            QuizQuestion.objects.create(mission=self.mission, text=f'질문 {i}', choice1='정답', choice2='오답', answer=1)

    def draw(self, offset):
        with patch('missions.quiz_rotation.timezone.localdate', return_value=timezone.now().date()+timedelta(days=offset)):
            return selected_questions(self.user, self.mission, create=True)

    def test_daily_draw_is_stable(self):
        self.assertEqual([q.pk for q in self.draw(0)], [q.pk for q in self.draw(0)])

    def test_no_repeat_until_exhaustion(self):
        first, second, last = self.draw(0), self.draw(1), self.draw(2)
        texts = [q.text for q in first+second+last]
        self.assertEqual(len(texts), 7)
        self.assertEqual(len(set(texts)), 7)
        self.assertEqual(len(self.draw(3)), 3)

    def test_submit_cannot_create_draw(self):
        self.assertEqual(selected_questions(self.user, self.mission), [])
        self.assertFalse(QuizDraw.objects.filter(user=self.user).exists())

    def test_duplicate_texts_across_missions_not_reused(self):
        other = Mission.objects.create(title='Other', category='testrotation', mission_type='quiz')
        QuizQuestion.objects.create(mission=other, text='질문 0', choice1='정답', choice2='오답', answer=1)
        self.draw(0); self.draw(1); self.draw(2)
        self.assertEqual(len(QuizHistory.objects.get(user=self.user, category='testrotation').seen_texts), 7)

    def test_history_is_per_user(self):
        self.draw(0)
        other = User.objects.create_user(username='other')
        self.assertEqual(len(selected_questions(other, self.mission, create=True)), 3)
        self.assertEqual(QuizHistory.objects.filter(category='testrotation').count(), 2)

    def test_same_category_draws_share_history(self):
        a = self.draw(0)
        other = Mission.objects.create(title='Other', category='testrotation', mission_type='quiz')
        b = selected_questions(self.user, other, create=True)
        self.assertFalse(set(q.text for q in a) & set(q.text for q in b))

    def test_bank_seeded_for_three_categories(self):
        for category in ('observation', 'microbe', 'local'):
            self.assertGreaterEqual(QuizQuestion.objects.filter(mission__category=category).count(), 12)
