# AI Agents Lecture

Materials for a three-part Berkeley lecture on building, evaluating, and deploying AI agents.

## Lecture structure

| Part | Topic | Lead |
|---|---|---|
| 1 | Coding with AI agents | Eloi Pereira |
| 2 | Validation and evaluation | Christian |
| 3 | Deployment | Alex |

The parts are loosely coupled. They share a running example, and each part can use as much or as little of it as it needs.

## Running example: a quiz generator

An AI agent reads the slides from Part 1 and generates a multiple-choice quiz. Every question must cite a verbatim quote from the slides, so grounding can be checked by code.

Part 1 builds it live in three versions:

| Version | Design | Who owns the control flow |
|---|---|---|
| v0 | Single structured LLM call | Nobody |
| v1 | Agent loop with a validator | The model |
| v2 | Agent graph: concepts, questions, critic, assembly | The program |

The harness is plain Python, with no agent framework. Models run locally through Ollama and can be swapped with one environment variable, which makes model comparison part of the exercise.

Possible hooks for the other parts:

- **Evaluation:** grounding, ambiguity, guessability, loop vs graph, model vs model. Every run writes a trace to `runs/`.
- **Deployment:** hardware requirements for a given model and application, edge and IoT, robotics.

## Repository layout

```
slides/
  lecture.md    # Part 1 slides (Marp); also the quiz generator's input
  img/          # SVG diagrams used by the slides
```

The application code, tests, run traces, and Claude Code configuration are added during the live build.

## Viewing the slides

The slides are plain Markdown with [Marp](https://marp.app) front matter. Open them with the Marp extension for VS Code, or render them from the command line:

```bash
npx @marp-team/marp-cli@latest slides/lecture.md --html
```

The HTML file is written next to `lecture.md` so it can find the diagrams in `slides/img/`. To export a PDF instead, add `--pdf --allow-local-files`. Speaker notes are HTML comments in the markdown; press `p` in the rendered HTML to open presenter view.

## Prerequisites for the live build

- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com), with at least one model that supports tool calling
- [Claude Code](https://code.claude.com)

## Running the quiz generator

From the repo root, with the Ollama server running:

```bash
uv sync                                              # install dependencies
uv run python -m quizgen.v0_single slides/lecture.md # v0: one structured call
uv run python -m quizgen.v1_loop slides/lecture.md   # v1: agent loop with a validator
uv run python -m quizgen.v2_graph slides/lecture.md  # v2: agent graph
```

Each command generates one quiz. The model defaults to `qwen3:8b`. Swap it with an environment
variable; nothing else changes:

```bash
QUIZGEN_MODEL=qwen3.5:4b uv run python -m quizgen.v2_graph slides/lecture.md
```

Each run writes the quiz to `data/quizes/<version>/quiz_<timestamp>.json` and appends a trace to
`runs/<version>.jsonl`. Every trace has the model, input hash, tokens, latency and the quiz. v1
adds `turns` and `unresolved`; v2 adds `concepts_found`, `revisions` and `unresolved`. Paths are
relative, so run from the repo root.

To generate several quizzes, loop:

```bash
for i in {1..5}; do uv run python -m quizgen.v1_loop slides/lecture.md; done
```

To run a version exactly as it was first built, check out its tag (`git checkout v1`). For how
each version works and how they compare, see [docs/comparison.md](docs/comparison.md).

Run the tests (no Ollama needed; the LLM is faked):

```bash
uv run pytest
```

## License

MIT. See [LICENSE](LICENSE).

## Part 2: validation

Part 2 checks what Part 1 built without changing it. See [docs/validation.md](docs/validation.md).

```bash
uv run python -m evals.quiz_eval slides/lecture.md --gate v2   # intent gates on saved quizzes
uv run python -m evals.mutate                                  # do the tests catch planted bugs?
EVAL_MODEL=llama3.2:3b uv run python -m evals.solver v2        # blind student (needs Ollama)
```
