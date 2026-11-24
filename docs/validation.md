# Part 2: validating what agents build

Part 1 ends with a question: *which version is better, and how would you know?* Part 2 answers
it in two layers, and adds the checks a team needs before agent-written code reaches production.

## Two loops, two questions

| | Verification (Part 1) | Validation (Part 2) |
|---|---|---|
| Question | Did we build it right? | Did we build the right thing? |
| Measured against | the spec in CLAUDE.md | the lecturer's intent |
| Where it runs | inside the agent's loop | outside, on the outputs |
| Example | every quote is verbatim | quizzes are fair, varied and not guessable |

The critic inside v2 is part of the product. The evaluator is not: it must not repeat the
critic's work, and the generator must never see the gates it is graded on.

## The pipeline: what is automated, what is human

| Step | Check | How | When | Cost |
|---|---|---|---|---|
| Design | Plan matches the intent | `designer` sub-agent writes it, **human approves** | before code | minutes of human time |
| Code | Lint, design rules | `lint.sh` hook, `reviewer` sub-agent | every edit, every version | seconds |
| Tests | Would the tests catch a bug? | `evals/mutate.py`, `test-auditor` sub-agent | every push (CI) | seconds |
| Security | Injection, secrets, weakened guard rails | `security-reviewer` sub-agent, **human signs off** | before merge | minutes |
| Output, spec | Schema, grounding | Part 1's checks (`is_grounded`) | every run | free |
| Output, intent | Fairness, variety, coverage, tells | `evals/quiz_eval.py --gate` | every PR | seconds |
| Output, intent | Guessable without the lecture? | `evals/solver.py` (a model call per question) | stage and prod pushes | minutes, tokens |
| Acceptance | Would I give this quiz to my class? | **lecturer reads a sample** | before release | human time |

## Results on Part 1's quizzes

Run: `python -m evals.quiz_eval slides/lecture.md` over the 5 saved quizzes per version.

| Gate | v0 | v1 | v2 |
|---|---|---|---|
| Grounded (all quotes verbatim) | 0.92 ✗ | 0.84 ✗ | **1.00** |
| Max share of one answer position (≤ 0.40) | 0.80 ✗ | 0.52 ✗ | **0.40** |
| Stem pastes the quote (≤ 0.20) | 0.04 | 0.16 | 0.76 ✗ |
| Stem cites a quote students never see (≤ 0.20) | 0.00 | 0.00 | 0.92 ✗ |
| Correct option is the longest (≤ 0.40) | 0.60 ✗ | 0.32 | 0.64 ✗ |
| Slides covered by at least one question (≥ 0.40) | 0.44 | 0.38 ✗ | 0.31 ✗ |

v2 passes every check it was built against and fails four of the lecturer's. The fixes belong
in the generator (write stems without the quote, vary option length, spread concepts across
slides), not in the gates.

## Testing the tests

`python -m evals.mutate` plants five plausible "helpful" edits. Part 1's tests catch 3 of 5:

- **Survived:** matching only the first six words of a quote. A real quote with an invented
  ending passes, which is exactly v1's failure mode. Killed by
  `test_fabricated_ending_is_not_grounded`.
- **Survived:** removing the shuffle in `assemble`. Answers stay balanced, but every quiz gets
  the same answer key. Killed by `test_answer_key_changes_between_quizzes`.

With `tests/test_validation_gaps.py` the score is 5 of 5.

## Caveats

- 5 quizzes per version is a trend, not a significant result. Re-run on fresh quizzes.
- The gates are heuristics a lecturer chose. They are a starting point to argue about, which is
  the point: intent has to be written down before it can be checked.
- An LLM grading LLM output is circular if it is the same model. `evals/solver.py` warns when
  `EVAL_MODEL` equals `QUIZGEN_MODEL`.
