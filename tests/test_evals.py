"""Part 2's eval code is code too: it gets tests. No model is called."""

import json
from dataclasses import dataclass

from evals import quiz_eval, solver

Q = {
    "concept": "agent",
    "stem": "What is an agent?",
    "options": ["A database", "A model using tools in a loop", "A compiler", "A GPU"],
    "answer_index": 1,
    "source_quote": "An agent is a model using tools in a loop.",
    "difficulty": "easy",
}


def test_stem_that_pastes_the_quote_is_flagged() -> None:
    leaky = Q | {"stem": "According to 'An agent is a model using tools in a loop', what is it?"}
    assert quiz_eval.stem_quotes_source(leaky)
    assert quiz_eval.stem_cites_quote(Q | {"stem": "According to the quote, what is an agent?"})
    assert not quiz_eval.stem_quotes_source(Q)
    assert not quiz_eval.stem_cites_quote(Q)


def test_longest_option_tell() -> None:
    assert quiz_eval.longest_is_answer(Q)
    short_answer = Q | {"options": ["A", "B is long", "C", "D"], "answer_index": 0}
    assert not quiz_eval.longest_is_answer(short_answer)


def test_invalid_question_is_caught() -> None:
    assert quiz_eval.is_valid(Q)
    assert not quiz_eval.is_valid(Q | {"options": ["A", "A", "B", "C"]})
    assert not quiz_eval.is_valid(Q | {"answer_index": 4})


def test_fairness_and_variety_across_quizzes() -> None:
    easy = [Q | {"difficulty": "easy"}] * 2
    hard = [Q | {"difficulty": "hard"}] * 2
    assert quiz_eval.difficulty_spread([easy, hard]) == 2
    assert quiz_eval.repeated_answer_keys([easy, hard]) == 1.0
    assert quiz_eval.cross_quiz_overlap([easy, hard]) == 1.0


def test_gate_failures_name_the_metric() -> None:
    metrics = {name: (1.0 if op == ">=" else 0.0) for name, (op, _) in quiz_eval.GATES.items()}
    assert quiz_eval.gate_failures(metrics) == []
    assert quiz_eval.gate_failures(metrics | {"grounded": 0.9})[0].startswith("grounded")


@dataclass
class Reply:
    text: str


class AlwaysPicks:
    """A fake blind student that always picks the option containing `word`."""

    def __init__(self, word: str) -> None:
        self.word = word

    def chat(self, messages: list[dict], schema: dict | None = None, tools=None) -> Reply:
        prompt = messages[0]["content"].splitlines()
        lines = [line for line in prompt if line[:2] in {"0.", "1.", "2.", "3."}]
        pick = next((i for i, line in enumerate(lines) if self.word in line), 0)
        return Reply(json.dumps({"answer_index": pick}))


def test_blind_solver_flags_a_guessable_question() -> None:
    assert solver.guessable(Q, AlwaysPicks("tools"))


def test_position_luck_is_not_guessable() -> None:
    """Always answering 1 is right in one order only; the reversed order exposes it."""

    class AlwaysOne:
        def chat(self, messages, schema=None, tools=None) -> Reply:
            return Reply(json.dumps({"answer_index": 1}))

    assert not solver.guessable(Q, AlwaysOne())
