import random
from django.db import transaction
from django.utils import timezone
from .models import QuizQuestion, QuizDraw, QuizHistory
from .learning import quiz_difficulty_for_level, user_garden_level


def selected_questions(user, mission, create=False):
    """同一日の再表示・再提出では固定。分野の未出題を使い切るまで再使用しない。"""
    with transaction.atomic():
        type(user).objects.select_for_update().get(pk=user.pk)
        garden_level = user_garden_level(user)
        difficulty, _ = quiz_difficulty_for_level(garden_level)
        draw = QuizDraw.objects.filter(user=user, mission=mission, date=timezone.localdate()).first()
        if draw:
            found = {q.pk:q for q in QuizQuestion.objects.filter(pk__in=draw.question_ids)}
            selected = [found[k] for k in draw.question_ids if k in found]
            if not create or (selected and all(q.difficulty_level == difficulty for q in selected)):
                return selected
            draw.delete()
        if not create:
            return []
        history, _ = QuizHistory.objects.get_or_create(user=user, category=mission.category)
        pool = list(QuizQuestion.objects.filter(
            mission__category=mission.category, mission__mission_type='quiz',
            mission__is_active=True, difficulty_level=difficulty,
        ).order_by('pk'))
        if not pool:
            # 해당 난이도 문제가 아직 준비되지 않은 분야는 기존 문제를 보여 줘요.
            pool = list(QuizQuestion.objects.filter(
                mission__category=mission.category, mission__mission_type='quiz',
                mission__is_active=True,
            ).order_by('pk'))
        # 内容の重複も除く（別ミッションに同じ問題が登録されている場合）。
        pool = list({q.text:q for q in pool}.values())
        seen = set(history.seen_texts)
        fresh = [q for q in pool if q.text not in seen]
        if not fresh:
            fresh = pool
            seen = set()
        random.SystemRandom().shuffle(fresh)
        chosen = fresh[:3]
        if not chosen:
            return []
        history.seen_texts = sorted(seen | {q.text for q in chosen})
        history.save(update_fields=['seen_texts'])
        QuizDraw.objects.create(user=user, mission=mission, date=timezone.localdate(), question_ids=[q.pk for q in chosen])
        return chosen
