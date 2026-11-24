# CLAUDE.md

Materials for Part 1 ("Coding with AI agents") of a three-part Berkeley lecture.
Part 1 is 90 minutes: ~20 min of slides, ~70 min building a quiz generator live with Claude Code.
Part 2 (evaluation) and Part 3 (deployment) are led by colleagues and only consume this repo.

This file is shown on screen during the lecture. Keep it short and accurate.

## The app: a quiz generator

- **Input:** `slides/lecture.md` (the Part 1 slides, Marp markdown).
- **Output:** a multiple-choice quiz. Every question cites a verbatim `source_quote` from the input,
  so grounding is checkable by code.
- **Three versions**, each motivated by a visible failure of the previous one:

| Version | File | Design | Who owns control flow |
|---|---|---|---|
| v0 | `quizgen/v0_single.py` | One structured-output call | Nobody |
| v1 | `quizgen/v1_loop.py` | Loop: model submits via a tool, validator feeds errors back | The model |
| v2 | `quizgen/v2_graph.py` | Graph: extract concepts → fan-out questions → critic → revise → assemble | The program |

## Target layout

```
slides/lecture.md      # slides; also the quiz input
slides/img/            # SVG diagrams used by the slides
quizgen/
  schema.py            # Pydantic models: the contract (Question, Quiz)
  llm.py               # the only module that talks to Ollama
  grounding.py         # is_grounded(quote, source): deterministic; tool in v1, gate in v2, eval later
  assemble.py          # deterministic: shuffle options, balance answer positions and difficulty
  trace.py             # writes one JSONL record per run to runs/
  v0_single.py
  v1_loop.py
  v2_graph.py
tests/                 # written before the code they test
runs/                  # JSONL traces handed to Part 2
```

## Design rules

- **Plain Python, no agent framework.** Nodes are functions, edges are control flow, fan-out is
  `asyncio.gather`. Mention LangGraph / pydantic-ai on stage, don't depend on them.
- **Local models via Ollama.** Model is selected by the `QUIZGEN_MODEL` env var; nothing else
  changes when swapping models. Only `llm.py` imports the Ollama client.
- **Schema is the contract.** `Question` has `concept`, `stem`, `options` (exactly 4),
  `answer_index` (0–3), `source_quote`, `difficulty` (easy|medium|hard).
- **Verifiers over instructions.** Fix failures with checks (schema, `is_grounded`) and code
  (`assemble` fixes answer-position bias), not with prompt wording.
- **Every run is traced.** Each record: version, model, input hash, tokens, latency, turns or
  revision counts, unresolved questions, and the quiz. Part 2 compares v1 vs v2 and models from these.
- **No eval code here.** Evaluation is Part 2. Keep `is_grounded` reusable, but don't build judges
  or solvers.

## Stage constraints

- Code is read on a projector: whole app ≈ 300 lines, short functions, no clever abstractions.
  Readability on stage beats architectural purity.
- Each version must run end to end on a laptop with a small local model in under ~2 minutes.
- Git tags `v0`, `v1`, `v2` are the fallback when a live step derails. Never rewrite tagged history.
- `slides/lecture.md` is both slides and test input; edits change quiz outputs. The slides carry
  little text, so the speaker notes (HTML comments) are most of what the quiz can quote. Keep
  slides within the 20-minute budget.

## Commands

```bash
uv sync                                    # install
uv run pytest                              # tests (no Ollama needed; LLM calls are faked)
uv run ruff check && uv run ruff format    # lint/format
QUIZGEN_MODEL=qwen3:8b uv run python -m quizgen.v1_loop slides/lecture.md
npx @marp-team/marp-cli@latest slides/lecture.md --html   # render slides
```

Tests must not call a real model: inject a fake LLM into the code under test.

## Validation (Part 2)

Part 2 adds checks on top of Part 1 without changing Part 1's code.

- **Design first:** for a new feature, use the `designer` sub-agent and wait for a human to
  approve the plan in `docs/plans/`. Read approved plans before reading code; they are the
  project's memory.
- **Before you say a version is done:** run the `test-auditor` and `security-reviewer`
  sub-agents, then generate 5 quizzes and run the `evaluator` sub-agent. Report its verdict.
- **Never edit a gate in `evals/` to make a run pass.** Gates change only in a reviewed PR.
- **Cost tiers:** `evals/quiz_eval.py` is deterministic and cheap (every PR).
  `evals/solver.py` calls a model per question (stage and prod pushes only).

```bash
uv run python -m evals.quiz_eval slides/lecture.md --gate v2   # intent gates
uv run python -m evals.mutate                                  # do the tests catch bugs?
EVAL_MODEL=llama3.2:3b uv run python -m evals.solver v2        # blind student (slow)
```
