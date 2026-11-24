# 0001: Evaluate quizzes against the lecturer's intent

Status: Approved by Christian Manasseh, 2026-11-20

## Goal
Part 1's checks prove each quiz meets the spec. A lecturer also needs to know whether the
quizzes are fair to every group of students, varied, and not answerable without the lecture.

## Spec
- Reads `data/quizes/` and `runs/`; never modifies Part 1 code or outputs.
- Re-checks the schema and grounding independently of the generator.
- Gates: answer position ≤ 40%, no repeated answer keys, stems that paste or cite the quote
  ≤ 20%, longest-option tell ≤ 40%, difficulty spread ≤ 0.5, slide coverage ≥ 40%.
- Deterministic eval exits 1 on a failed gate; runs on every PR.
- Model-based eval uses a different model from the generator; runs on stage and prod only.

## Files
Add `evals/`, `tests/test_evals.py`, `tests/test_validation_gaps.py`, four sub-agents,
`.github/workflows/`. Do not change `quizgen/`.

## Tests first
Each metric gets a unit test on a hand-made question. The blind solver is tested with a fake
model, including one that always picks the same position.

## Evaluation
Run on Part 1's 15 saved quizzes; the report must explain the difference between v1 and v2.

## Risks
Gates encode one lecturer's judgement; review them with the teaching team. LLM judges can be
circular and position-biased; mitigated by a second model and a reversed option order.
