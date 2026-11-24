"""Test the tests: plant a small, plausible bug and check that at least one test fails.

When an agent writes the code it usually writes the tests too, so "all tests pass" proves
little on its own. A mutant that survives (every test still passes) marks behaviour that no
test protects. Each mutant below is an edit a helpful agent could plausibly make.

    python -m evals.mutate                                    # whole suite
    python -m evals.mutate --tests tests/test_grounding.py    # only Part 1's grounding tests
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Mutant:
    """Replace `find` with `replace` in `file`; `why` is the agent's plausible excuse."""

    file: str
    find: str
    replace: str
    why: str


GROUNDED = 'return " ".join(quote.split()) in " ".join(source.split())'

MUTANTS = [
    Mutant(
        "quizgen/grounding.py",
        GROUNDED,
        'return " ".join(quote.lower().split()) in " ".join(source.lower().split())',
        "make the quote match case-insensitive",
    ),
    Mutant(
        "quizgen/grounding.py",
        GROUNDED,
        'return " ".join(quote.split()[:6]) in " ".join(source.split())',
        "speed up: only match the first six words",
    ),
    Mutant(
        "quizgen/assemble.py",
        "rng.shuffle(positions)",
        "pass  # shuffle removed",
        "remove a shuffle that looks redundant",
    ),
    Mutant(
        "quizgen/assemble.py",
        "wrong.insert(position, correct)",
        "wrong.insert(0, correct)",
        "simplify: always put the answer first",
    ),
    Mutant(
        "quizgen/assemble.py",
        "sorted(placed, key=lambda q: DIFFICULTY_ORDER[q.difficulty])",
        "placed",
        "keep the order the writers returned",
    ),
]


def survives(mutant: Mutant, test_cmd: list[str]) -> bool:
    """Apply the mutant, run the tests, always restore the file. True if no test failed."""
    path = Path(mutant.file)
    original = path.read_bytes()  # bytes, so the restore is exact (line endings too)
    text = original.decode()
    if mutant.find not in text:
        msg = f"{mutant.file}: text to mutate not found: {mutant.find!r}"
        raise ValueError(msg)
    try:
        path.write_bytes(text.replace(mutant.find, mutant.replace, 1).encode())
        result = subprocess.run(test_cmd, capture_output=True, check=False)
        return result.returncode == 0
    finally:
        path.write_bytes(original)


def main() -> None:
    """Run every mutant and print which ones the tests caught."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tests", nargs="*", default=["tests"], help="test files or folders")
    parser.add_argument("--runner", default=f"{sys.executable} -m pytest -q -x", help="command")
    args = parser.parse_args()
    test_cmd = args.runner.split() + args.tests

    survivors = 0
    for m in MUTANTS:
        alive = survives(m, test_cmd)
        survivors += alive
        print(f"{'SURVIVED' if alive else 'killed  '}  {m.file:22} {m.why}")
    caught = len(MUTANTS) - survivors
    print(f"\nmutation score: {caught}/{len(MUTANTS)} caught")
    sys.exit(1 if survivors else 0)


if __name__ == "__main__":
    main()
