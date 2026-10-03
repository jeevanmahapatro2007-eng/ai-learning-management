"""Thin wrappers so other apps don't need to import engine internals directly."""
from . import engine


def process_quiz_result(quiz_result):
    engine.update_skills_from_quiz_result(quiz_result)
    engine.generate_recommendations(quiz_result.student)


def refresh_recommendations(student):
    return engine.generate_recommendations(student)


def get_insights(student):
    return engine.generate_insights(student)
