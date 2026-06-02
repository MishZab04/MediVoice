from .questions import QUESTION_ORDER


def get_first_question() -> str:
    return QUESTION_ORDER[0]


def get_next_question(current_key: str) -> str | None:
    """Return the next question key, or None if the assessment is complete."""
    try:
        idx = QUESTION_ORDER.index(current_key)
    except ValueError:
        return None
    next_idx = idx + 1
    if next_idx >= len(QUESTION_ORDER):
        return None
    return QUESTION_ORDER[next_idx]


def is_complete(current_key: str) -> bool:
    return get_next_question(current_key) is None
