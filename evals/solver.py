"""Expensive tier: a blind student. Can a model answer the quiz without the lecture?

A model that never saw the slides answers each question twice, with the options in the
given order and reversed. Right both times means the question tests general knowledge or
test-taking tricks, not the lecture. One model call per question per order, so CI runs this
only on pushes to stage and prod, never on every commit.

    EVAL_MODEL=llama3.2:3b python -m evals.solver v2
"""

import json
import os
import sys
from pathlib import Path

from evals.quiz_eval import REPORT_DIR, load_quizzes

GATE = 0.30  # a blind guesser who is right in both orders by luck: 1/16, about 6%

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"answer_index": {"type": "integer", "minimum": 0, "maximum": 3}},
    "required": ["answer_index"],
}
PROMPT = """You are a student who has NOT seen the lecture. Answer this question anyway.
Question: {stem}
Options:
{options}
Reply with the index (0-3) of the option you would pick."""


def answer(llm, stem: str, options: list[str]) -> int:
    """One blind attempt: the model sees the question and the options, nothing else."""
    listed = "\n".join(f"{i}. {o}" for i, o in enumerate(options))
    prompt = PROMPT.format(stem=stem, options=listed)
    reply = llm.chat([{"role": "user", "content": prompt}], ANSWER_SCHEMA)
    return json.loads(reply.text)["answer_index"]


def guessable(q: dict, llm) -> bool:
    """Right in both option orders: knowledge or a tell, not position luck."""
    right = q["answer_index"]
    forward = answer(llm, q["stem"], q["options"]) == right
    backward = answer(llm, q["stem"], q["options"][::-1]) == len(q["options"]) - 1 - right
    return forward and backward


def run(version: str, llm) -> dict:
    """Blind-solve every saved question of a version."""
    questions = [q for quiz in load_quizzes(version) for q in quiz]
    flags = [guessable(q, llm) for q in questions]
    return {
        "version": version,
        "questions": len(questions),
        "guessable": sum(flags) / len(questions),
        "examples": [q["stem"] for q, f in zip(questions, flags, strict=True) if f][:3],
    }


def main() -> None:
    """Solve one version's quizzes; exit 1 if too many are guessable."""
    from quizgen.llm import OllamaLLM, model_name  # noqa: PLC0415 - tests never need Ollama

    version = sys.argv[1]
    judge = os.environ.get("EVAL_MODEL", model_name())
    if judge == model_name():
        print(f"warning: {judge} wrote these questions and is now grading them (circular)")
    result = run(version, OllamaLLM(judge)) | {"judge_model": judge}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    Path(REPORT_DIR / f"solver_{version}.json").write_text(json.dumps(result, indent=2))
    print(f"{version}: {result['guessable']:.0%} guessable without the lecture (gate {GATE:.0%})")
    sys.exit(1 if result["guessable"] > GATE else 0)


if __name__ == "__main__":
    main()
