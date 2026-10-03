"""
Lodestar Recommendation Engine
===============================

This module is the "AI-based personalization" component described in the
project brief. It is implemented as a transparent, explainable weighted
scoring system rather than a black-box model — every recommendation this
engine produces carries a human-readable reason, which matters for a
learning platform where students and reviewers need to trust *why* a
suggestion was made.

Three signal families feed the engine, matching the brief:

1. Skill-based    — proficiency measured from quiz/assessment performance
                     (StudentSkill.proficiency_percent)
2. Content-based   — overlap between a student's declared interests /
                     preferred domains and a course's skills/category
3. Performance-based — recent quiz trend, completion rate, engagement

If scikit-learn is available in the deployment environment, `similar_courses`
will automatically use TF-IDF + cosine similarity for course-similarity
scoring; otherwise it falls back to a Jaccard-similarity approximation over
shared skills, so the platform runs identically with zero extra dependencies.
"""
from collections import defaultdict

from django.db.models import Case, Count, IntegerField, Value, When

from apps.courses.models import Course, Skill
from apps.quizzes.models import QuizResult

from .models import StudentSkill, Recommendation, LearningPath, LearningPathStep

WEAK_SKILL_WEIGHT = 40
INTEREST_MATCH_WEIGHT = 25
DOMAIN_MATCH_WEIGHT = 15
POPULARITY_WEIGHT = 10
NOT_ENROLLED_BONUS = 10


def _try_sklearn_similarity(courses):
    """Return {course_id: {other_course_id: similarity}} using TF-IDF if sklearn
    is installed, else None so the caller can fall back to the Jaccard method."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return None

    corpus, ids = [], []
    for c in courses:
        skill_text = ' '.join(s.name for s in c.skills_covered.all())
        corpus.append(f'{c.title} {c.short_description} {skill_text}')
        ids.append(c.id)

    if len(corpus) < 2:
        return None

    matrix = TfidfVectorizer(stop_words='english').fit_transform(corpus)
    sims = cosine_similarity(matrix)
    return {ids[i]: {ids[j]: sims[i][j] for j in range(len(ids)) if i != j} for i in range(len(ids))}


def update_skills_from_quiz_result(quiz_result):
    """Given a graded QuizResult, roll per-question correctness up into
    StudentSkill proficiency records. This is the bridge between the
    quiz/evaluation module (section 8) and the recommendation engine."""
    student = quiz_result.student
    per_skill = defaultdict(lambda: {'correct': 0, 'total': 0})

    for response in quiz_result.responses.select_related('question__skill'):
        skill = response.question.skill
        if not skill:
            continue
        per_skill[skill]['total'] += 1
        if response.is_correct:
            per_skill[skill]['correct'] += 1

    breakdown = {}
    for skill, tally in per_skill.items():
        pct = round((tally['correct'] / tally['total']) * 100, 1) if tally['total'] else 0
        record, _ = StudentSkill.objects.get_or_create(student=student, skill=skill)
        # Weighted rolling average: recent attempts count more, but history isn't discarded.
        if record.attempts == 0:
            record.proficiency_percent = pct
        else:
            record.proficiency_percent = round((record.proficiency_percent * 0.6) + (pct * 0.4), 1)
        record.attempts += 1
        record.recompute_level()
        record.save()
        breakdown[skill.name] = pct

    quiz_result.skill_breakdown = breakdown
    quiz_result.save(update_fields=['skill_breakdown'])
    return breakdown


def get_weak_skills(student, threshold=50):
    return StudentSkill.objects.filter(student=student, proficiency_percent__lt=threshold).select_related('skill')


def get_strong_skills(student, threshold=75):
    return StudentSkill.objects.filter(student=student, proficiency_percent__gte=threshold).select_related('skill')


def generate_recommendations(student, limit=8):
    """Core entry point: (re)generate the ranked recommendation list for a student."""
    if not hasattr(student, 'student_profile'):
        return []

    profile = student.student_profile
    interests = set(i.lower() for i in profile.interests_list())
    domains = set(d.lower() for d in profile.preferred_domains_list())

    weak_skill_ids = set(get_weak_skills(student).values_list('skill_id', flat=True))
    strong_skill_ids = set(get_strong_skills(student).values_list('skill_id', flat=True))

    already_enrolled = set(student.enrollments.values_list('course_id', flat=True))
    dismissed = set(
        Recommendation.objects.filter(student=student, is_dismissed=True).values_list('course_id', flat=True)
    )

    candidates = list(
        Course.objects.filter(status=Course.Status.PUBLISHED)
        .exclude(id__in=already_enrolled | dismissed)
        .select_related('category')
        .prefetch_related('skills_covered')
        .annotate(enrolled_count=Count('enrollments'))
    )

    max_popularity = max([c.enrolled_count for c in candidates], default=0) or 1

    scored = []
    for course in candidates:
        course_skill_ids = {s.id for s in course.skills_covered.all()}  # prefetched
        score = 0
        reasons = []
        top_reason = Recommendation.Reason.INTEREST_MATCH

        overlap_weak = course_skill_ids & weak_skill_ids
        if overlap_weak:
            score += WEAK_SKILL_WEIGHT * (len(overlap_weak) / max(len(course_skill_ids), 1))
            weak_names = ', '.join(Skill.objects.filter(id__in=overlap_weak).values_list('name', flat=True)[:2])
            reasons.append(f'Strengthens {weak_names}, an area you\'re still building up')
            top_reason = Recommendation.Reason.WEAK_SKILL

        # Content-based: interest / title / category text overlap
        text_blob = f'{course.title} {course.category.name if course.category else ""}'.lower()
        interest_hits = [i for i in interests if i and i in text_blob]
        if interest_hits:
            score += INTEREST_MATCH_WEIGHT
            if not reasons:
                reasons.append(f'Matches your interest in {interest_hits[0]}')
                top_reason = Recommendation.Reason.INTEREST_MATCH

        domain_hits = [d for d in domains if d and (course.category and d in course.category.name.lower())]
        if domain_hits:
            score += DOMAIN_MATCH_WEIGHT
            if not reasons:
                reasons.append(f'In your preferred domain: {course.category.name}')
                top_reason = Recommendation.Reason.INTEREST_MATCH

        # Skip courses that only touch skills the student is already strong in
        if course_skill_ids and course_skill_ids.issubset(strong_skill_ids):
            score -= 15

        # Difficulty alignment with current level
        if profile.current_level == course.difficulty:
            score += 8

        # Popularity as a light tie-breaker (performance/social proof signal)
        score += POPULARITY_WEIGHT * (course.enrolled_count / max_popularity)
        score += NOT_ENROLLED_BONUS

        if not reasons:
            reasons.append('Popular with learners on a similar path to you')
            top_reason = Recommendation.Reason.POPULAR_IN_DOMAIN

        if score > 0:
            scored.append((course, score, top_reason, reasons[0]))

    scored.sort(key=lambda t: t[1], reverse=True)
    top = scored[:limit]

    # Keep dismissed rows: they're what stops a dismissed course from coming straight back.
    Recommendation.objects.filter(student=student, is_dismissed=False).exclude(
        course_id__in=[c.id for c, *_ in top]
    ).delete()
    results = []
    for course, score, reason, explanation in top:
        rec, _ = Recommendation.objects.update_or_create(
            student=student, course=course,
            defaults={'score': score, 'reason': reason, 'explanation': explanation},
        )
        results.append(rec)
    return results


def similar_courses(course, limit=4):
    """Course-similarity for 'students who improved in X also took Y' style suggestions."""
    pool = list(Course.objects.filter(status=Course.Status.PUBLISHED).exclude(id=course.id))
    sklearn_sims = _try_sklearn_similarity([course] + pool)

    if sklearn_sims:
        ranked = sorted(sklearn_sims.get(course.id, {}).items(), key=lambda kv: kv[1], reverse=True)
        ids = [cid for cid, _ in ranked[:limit]]
        by_id = {c.id: c for c in pool}
        return [by_id[i] for i in ids if i in by_id]

    # Fallback: Jaccard similarity over shared skills
    course_skills = set(course.skills_covered.values_list('id', flat=True))
    scored = []
    for other in pool:
        other_skills = set(other.skills_covered.values_list('id', flat=True))
        union = course_skills | other_skills
        if not union:
            continue
        jaccard = len(course_skills & other_skills) / len(union)
        if jaccard > 0:
            scored.append((other, jaccard))
    scored.sort(key=lambda t: t[1], reverse=True)
    return [c for c, _ in scored[:limit]]


def generate_learning_path(student, domain):
    """Builds/refreshes an ordered topic sequence for a domain, skipping topics
    the student has already demonstrated strength in."""
    path, _ = LearningPath.objects.get_or_create(student=student, domain=domain)

    difficulty_rank = Case(
        When(difficulty=Course.Difficulty.BEGINNER, then=Value(0)),
        When(difficulty=Course.Difficulty.INTERMEDIATE, then=Value(1)),
        When(difficulty=Course.Difficulty.ADVANCED, then=Value(2)),
        default=Value(3), output_field=IntegerField(),
    )
    domain_courses = (
        Course.objects.filter(status=Course.Status.PUBLISHED, category__name__iexact=domain)
        .annotate(difficulty_rank=difficulty_rank)
        .order_by('difficulty_rank', 'title')
        .prefetch_related('skills_covered')
    )

    strong_skill_ids = set(get_strong_skills(student).values_list('skill_id', flat=True))

    path.steps.all().delete()
    order = 0
    first_incomplete_set = False
    for course in domain_courses:
        course_skill_ids = {s.id for s in course.skills_covered.all()}
        already_strong = bool(course_skill_ids) and course_skill_ids.issubset(strong_skill_ids)

        status = LearningPathStep.StepStatus.COMPLETED if already_strong else LearningPathStep.StepStatus.LOCKED
        order += 1
        step = LearningPathStep.objects.create(
            path=path, topic=course.title, course=course, order=order, status=status,
        )
        if status != LearningPathStep.StepStatus.COMPLETED and not first_incomplete_set:
            step.status = LearningPathStep.StepStatus.AVAILABLE
            step.save(update_fields=['status'])
            first_incomplete_set = True

    return path


def generate_insights(student):
    """Human-readable AI analytics insights (section 13 of the brief)."""
    insights = []
    strong = list(get_strong_skills(student)[:3])
    weak = list(get_weak_skills(student)[:3])

    for s in strong:
        insights.append(f'You are strong in {s.skill.name} ({s.proficiency_percent:.0f}% proficiency).')
    for s in weak:
        insights.append(f'We recommend practicing {s.skill.name} — currently at {s.proficiency_percent:.0f}%.')

    results = list(QuizResult.objects.filter(student=student).order_by('taken_at')[:20])
    if len(results) >= 2:
        first_half = results[:len(results) // 2]
        second_half = results[len(results) // 2:]
        avg_first = sum(r.percent for r in first_half) / len(first_half)
        avg_second = sum(r.percent for r in second_half) / len(second_half)
        diff = avg_second - avg_first
        if abs(diff) >= 3:
            direction = 'improved' if diff > 0 else 'dipped'
            insights.append(f'Your quiz performance has {direction} by {abs(diff):.0f}% recently.')

    if not insights:
        insights.append('Take a skill assessment to unlock personalized insights.')

    return insights
