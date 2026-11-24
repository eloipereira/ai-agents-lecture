"""Evaluate quizzes against the lecturer's intent, not just the generator's spec.

Level 1 re-checks the spec independently: never trust the generator's own checks.
Level 2 asks what a lecturer cares about: is each quiz fair, varied and hard to guess?
Deterministic and cheap, so it can run on every pull request.

    python -m evals.quiz_eval slides/lecture.md             # report on every version
    python -m evals.quiz_eval slides/lecture.md --gate v2   # exit 1 if v2 misses a gate
"""

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from quizgen.grounding import is_grounded

QUIZ_DIR = Path("data/quizes")
RUNS_DIR = Path("runs")
REPORT_DIR = Path("evals/reports")
LEVEL = {"easy": 1, "medium": 2, "hard": 3}
STOPWORDS = {"a", "an", "the", "is", "are", "of", "to", "in", "on", "for", "and", "or", "by", "with", "what", "which", "who", "how", "does", "do", "it", "this", "that"}

# The lecturer's intent, written down as numbers. Change a gate in a reviewed pull request,
# never to make a failing run pass.
GATES = {
    "valid": (">=", 1.0),  # schema rules hold: 4 distinct options, answer index 0-3
    "grounded": (">=", 1.0),  # every quote is verbatim in the slides
    "max_answer_share": ("<=", 0.40),  # no answer position (A-D) holds more than 40%
    "repeated_answer_keys": ("<=", 0.0),  # no two quizzes share the same answer key
    "stem_quotes_source": ("<=", 0.20),  # the stem should not paste the quote
    "stem_cites_quote": ("<=", 0.20),  # "according to the quote...": students never see it
    "longest_is_answer": ("<=", 0.40),  # "pick the longest option" should not work
    "difficulty_spread": ("<=", 0.50),  # quiz-to-quiz gap in mean difficulty (1-3 scale)
    "cross_quiz_overlap": ("<=", 0.50),  # mean share of quotes two quizzes have in common
    "slide_coverage": (">=", 0.40),  # share of slides that at least one question tests
}


def words(text: str) -> list[str]:
    """Lower-case words without punctuation, for loose comparisons."""
    return re.findall(r"[a-z0-9%']+", text.lower())


def content_words(text: str) -> set[str]:
    """Words that carry meaning: no stopwords."""
    return {w for w in words(text) if w not in STOPWORDS}


def load_quizzes(version: str) -> list[list[dict]]:
    """Every saved quiz of a version, oldest first. A failed run saves null; skip it."""
    quizzes = []
    for path in sorted((QUIZ_DIR / version).glob("quiz_*.json")):
        data = json.loads(path.read_text())
        if data:
            quizzes.append(data["questions"])
    return quizzes


def load_traces(version: str) -> list[dict]:
    """The run traces Part 1 wrote: tokens, latency, turns."""
    path = RUNS_DIR / f"{version}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


# ---- Level 1: the spec, re-checked by code the generator never saw ----------------------


def is_valid(q: dict) -> bool:
    """The schema rules, checked again here rather than trusted."""
    options = q.get("options", [])
    return len(options) == 4 and len(set(options)) == 4 and q.get("answer_index") in range(4)


# ---- Level 2: the lecturer's intent ------------------------------------------------------


def stem_quotes_source(q: dict) -> bool:
    """The stem pastes the quote, so the question reads its own answer aloud."""
    return " ".join(words(q["source_quote"])) in " ".join(words(q["stem"]))


def stem_cites_quote(q: dict) -> bool:
    """The stem points at a quote ("according to the quote") the student will never see."""
    return re.search(r"\b(the|this) (quote|statement)\b", q["stem"].lower()) is not None


def longest_is_answer(q: dict) -> bool:
    """The correct option is strictly the longest: a classic test-writing tell."""
    lengths = [len(o) for o in q["options"]]
    right = lengths[q["answer_index"]]
    return all(right > n for i, n in enumerate(lengths) if i != q["answer_index"])


def answer_echoes_stem(q: dict) -> bool:
    """The correct option shares more words with the stem than any distractor does."""
    stem = content_words(q["stem"])
    overlap = [len(stem & content_words(o)) for o in q["options"]]
    right = overlap[q["answer_index"]]
    return right > 0 and all(right > n for i, n in enumerate(overlap) if i != q["answer_index"])


def slide_coverage(quizzes: list[list[dict]], source: str) -> float:
    """Share of slides that at least one question quotes. Slide 0 is the front matter."""
    slides = source.split("\n---\n")[1:]
    quotes = [q["source_quote"] for quiz in quizzes for q in quiz]
    covered = sum(any(is_grounded(quote, s) for quote in quotes) for s in slides)
    return covered / len(slides)


def cross_quiz_overlap(quizzes: list[list[dict]]) -> float:
    """Mean Jaccard overlap of the quotes used by each pair of quizzes."""
    sets = [{" ".join(words(q["source_quote"])) for q in quiz} for quiz in quizzes]
    pairs = [len(a & b) / len(a | b) for a, b in combinations(sets, 2)]
    return statistics.mean(pairs) if pairs else 0.0


def repeated_answer_keys(quizzes: list[list[dict]]) -> float:
    """Share of quizzes whose answer key (e.g. A-D-B-A-C) also appears in another quiz."""
    keys = Counter(tuple(q["answer_index"] for q in quiz) for quiz in quizzes)
    return sum(n for n in keys.values() if n > 1) / len(quizzes)


def difficulty_spread(quizzes: list[list[dict]]) -> float:
    """Gap between the easiest and the hardest quiz, by mean difficulty (1-3)."""
    means = [statistics.mean(LEVEL[q["difficulty"]] for q in quiz) for quiz in quizzes]
    return max(means) - min(means)


def share(questions: list[dict], test) -> float:
    """Fraction of questions for which `test` is true."""
    return sum(map(test, questions)) / len(questions)


def evaluate(version: str, source: str) -> dict:
    """All metrics for one version: spec, intent and cost."""
    quizzes = load_quizzes(version)
    questions = [q for quiz in quizzes for q in quiz]
    positions = Counter(q["answer_index"] for q in questions)
    traces = load_traces(version)
    return {
        "quizzes": len(quizzes),
        "questions": len(questions),
        "valid": share(questions, is_valid),
        "grounded": share(questions, lambda q: is_grounded(q["source_quote"], source)),
        "max_answer_share": max(positions.values()) / len(questions),
        "repeated_answer_keys": repeated_answer_keys(quizzes),
        "stem_quotes_source": share(questions, stem_quotes_source),
        "stem_cites_quote": share(questions, stem_cites_quote),
        "longest_is_answer": share(questions, longest_is_answer),
        "answer_echoes_stem": share(questions, answer_echoes_stem),
        "difficulty_spread": difficulty_spread(quizzes),
        "cross_quiz_overlap": cross_quiz_overlap(quizzes),
        "slide_coverage": slide_coverage(quizzes, source),
        "tokens_per_quiz": statistics.mean(t["input_tokens"] + t["output_tokens"] for t in traces)
        if traces
        else None,
        "latency_s_max": max((t["latency_s"] for t in traces), default=None),
    }


def gate_failures(metrics: dict) -> list[str]:
    """The gates this version misses, as readable lines."""
    failures = []
    for name, (op, limit) in GATES.items():
        value = metrics[name]
        ok = value >= limit if op == ">=" else value <= limit
        if not ok:
            failures.append(f"{name} = {value:.2f}, needs {op} {limit:.2f}")
    return failures


def report(results: dict[str, dict]) -> str:
    """A markdown table: one row per metric, one column per version."""
    versions = list(results)
    lines = [
        "| metric | gate | " + " | ".join(versions) + " |",
        "|---|---|" + "---|" * len(versions),
    ]
    for name in results[versions[0]]:
        gate = " ".join(map(str, GATES[name])) if name in GATES else ""
        cells = []
        for v in versions:
            value = results[v][name]
            text = str(value) if not isinstance(value, float) else f"{value:.2f}"
            failed = [f.split(" ")[0] for f in gate_failures(results[v])]
            if name in failed:
                text += " ✗"
            cells.append(text)
        lines.append(f"| {name} | {gate} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    """Evaluate every version found in data/quizes; optionally gate one of them."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="the slides the quizzes were generated from")
    parser.add_argument("--gate", help="exit 1 if this version misses any gate")
    args = parser.parse_args()

    source = args.source.read_text()
    versions = sorted(p.name for p in QUIZ_DIR.iterdir() if p.is_dir())
    results = {v: evaluate(v, source) for v in versions}
    table = report(results)
    print(table)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "latest.md").write_text(table + "\n")
    (REPORT_DIR / "latest.json").write_text(json.dumps(results, indent=2))

    if args.gate:
        failures = gate_failures(results[args.gate])
        print(f"\n{args.gate}: " + ("all gates pass" if not failures else "FAILED"))
        for line in failures:
            print(f"  - {line}")
        sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
