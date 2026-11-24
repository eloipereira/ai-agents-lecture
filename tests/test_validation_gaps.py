"""Tests added in Part 2. Each one kills a mutant that Part 1's tests let survive."""

import random

from quizgen.assemble import assemble
from quizgen.grounding import is_grounded
from quizgen.schema import Question

SOURCE = "An agent is a model using tools in a loop. The harness is everything else."


def test_fabricated_ending_is_not_grounded() -> None:
    """A true opening glued to an invented ending is still an invented quote."""
    assert not is_grounded("An agent is a model using a database to store facts.", SOURCE)


def question(i: int, difficulty: str) -> Question:
    return Question(
        concept=f"c{i}",
        stem=f"Question {i}?",
        options=[f"right {i}", f"wrong {i}a", f"wrong {i}b", f"wrong {i}c"],
        answer_index=0,
        source_quote="a quote of at least five words",
        difficulty=difficulty,
    )


QUESTIONS = [question(i, d) for i, d in enumerate(["easy", "medium", "hard", "easy", "medium"])]


def test_answer_key_changes_between_quizzes() -> None:
    """Students who share answer keys must not be able to share them across quizzes."""
    keys = {
        tuple(q.answer_index for q in assemble(QUESTIONS, random.Random(seed)).questions)
        for seed in range(20)
    }
    assert len(keys) > 1
