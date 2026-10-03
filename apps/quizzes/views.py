from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from .forms import QuizForm, QuestionForm, AnswerFormSet
from .models import Quiz, Question, Answer, QuizResult, QuestionResponse
from apps.recommendations.services import process_quiz_result
from apps.notifications.services import notify
from apps.gamification.services import check_quiz_badges


@login_required
def quiz_list(request):
    quizzes = Quiz.objects.filter(quiz_type=Quiz.QuizType.SKILL_ASSESSMENT).annotate(qcount=Count('questions'))
    course_quizzes = Quiz.objects.exclude(quiz_type=Quiz.QuizType.SKILL_ASSESSMENT).annotate(qcount=Count('questions'))
    return render(request, 'quizzes/quiz_list.html', {'assessments': quizzes, 'course_quizzes': course_quizzes})


@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.prefetch_related('answers')

    if request.method == 'POST':
        with transaction.atomic():
            score = 0
            total = 0
            responses_to_create = []

            result = QuizResult.objects.create(
                student=request.user, quiz=quiz,
                attempt_number=QuizResult.objects.filter(student=request.user, quiz=quiz).count() + 1,
            )

            for question in questions:
                total += question.points
                answers_by_id = {a.id: a for a in question.answers.all()}  # uses the prefetch, no extra query
                selected_answer = None
                try:
                    selected_answer = answers_by_id.get(int(request.POST.get(f'question_{question.id}', '')))
                except (TypeError, ValueError):
                    pass  # unanswered, or a tampered non-numeric value
                is_correct = bool(selected_answer and selected_answer.is_correct)
                if is_correct:
                    score += question.points
                responses_to_create.append(QuestionResponse(
                    quiz_result=result, question=question, selected_answer=selected_answer, is_correct=is_correct,
                ))

            QuestionResponse.objects.bulk_create(responses_to_create)

            percent = round((score / total) * 100, 1) if total else 0
            result.score_points = score
            result.total_points = total
            result.percent = percent
            result.passed = percent >= quiz.pass_mark_percent
            result.save()

            process_quiz_result(result)
            check_quiz_badges(request.user)

            notify(
                request.user,
                title='Quiz graded',
                message=f'You scored {percent:.0f}% on "{quiz.title}".',
                category='quiz',
            )

        return redirect('quizzes:result', pk=result.pk)

    return render(request, 'quizzes/take_quiz.html', {'quiz': quiz, 'questions': questions})


@login_required
def quiz_result(request, pk):
    result = get_object_or_404(QuizResult, pk=pk, student=request.user)
    responses = result.responses.select_related('question', 'selected_answer').prefetch_related('question__answers')
    return render(request, 'quizzes/quiz_result.html', {'result': result, 'responses': responses})


@login_required
def quiz_history(request):
    results = QuizResult.objects.filter(student=request.user).select_related('quiz')
    return render(request, 'quizzes/quiz_history.html', {'results': results})


# ---------------------------------------------------------------------------
# Instructor quiz building
# ---------------------------------------------------------------------------

@login_required
def instructor_quiz_list(request):
    if not request.user.is_instructor:
        return HttpResponseForbidden('Instructor access only.')
    quizzes = Quiz.objects.filter(created_by=request.user).annotate(qcount=Count('questions'))
    return render(request, 'quizzes/instructor_quiz_list.html', {'quizzes': quizzes})


@login_required
def quiz_create(request):
    if not request.user.is_instructor:
        return HttpResponseForbidden('Instructor access only.')
    if request.method == 'POST':
        form = QuizForm(request.POST, user=request.user)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            form.save_m2m()
            messages.success(request, 'Quiz created. Now add questions.')
            return redirect('quizzes:instructor_questions', pk=quiz.pk)
    else:
        form = QuizForm(user=request.user)
    return render(request, 'quizzes/quiz_form.html', {'form': form})


@login_required
def instructor_questions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if quiz.created_by != request.user:
        return HttpResponseForbidden('You do not own this quiz.')

    if request.method == 'POST':
        qform = QuestionForm(request.POST)
        if qform.is_valid():
            question = qform.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'Question added. Now add its answer options below.')
            return redirect('quizzes:instructor_answers', quiz_pk=pk, question_pk=question.pk)
    else:
        qform = QuestionForm()

    return render(request, 'quizzes/instructor_questions.html', {
        'quiz': quiz, 'questions': quiz.questions.prefetch_related('answers'), 'form': qform,
    })


@login_required
def instructor_answers(request, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    if quiz.created_by != request.user:
        return HttpResponseForbidden('You do not own this quiz.')
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)

    if request.method == 'POST':
        formset = AnswerFormSet(request.POST, instance=question, prefix='answers')
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Answers saved.')
            return redirect('quizzes:instructor_questions', pk=quiz.pk)
    else:
        formset = AnswerFormSet(instance=question, prefix='answers')

    return render(request, 'quizzes/instructor_answers.html', {
        'quiz': quiz, 'question': question, 'formset': formset,
    })
