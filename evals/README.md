# evals/: Part 2

| File | What it checks | Cost |
|---|---|---|
| `quiz_eval.py` | Spec (again) and intent: fairness, variety, coverage, tells | seconds, no model |
| `mutate.py` | Whether the tests catch plausible bugs | seconds, no model |
| `solver.py` | Whether a model can answer without the lecture | one model call per question per order |

See [docs/validation.md](../docs/validation.md) for the pipeline and the results.
