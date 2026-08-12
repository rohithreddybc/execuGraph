# ExecuGraph

Code, data and result logs for the paper *Execution Feedback, Not Role
Decomposition: A Controlled Comparison of Single- and Multi-Agent LLM Code
Synthesis*.

ExecuGraph splits code generation across six agents (Planner, Code Generator,
Logical Reviewer, Evaluator, Optimizer, Explainer) wired together by a compiled
LangGraph workflow over typed shared state. Whether a program is accepted is
decided by running it in a sandbox, never by a model's opinion of it, and a
bounded retry loop feeds runtime errors back to the Generator.

The framework exists mainly as a measuring instrument. One codebase collapses
by configuration into a single-agent one-shot run, a single-agent
execution-retry run, and the full multi-agent pipeline, so the contribution of
role decomposition can be separated from the contribution of execution feedback
instead of being confounded with it.

## Headline result

On the full 164-problem HumanEval suite, the only benchmark here with enough
paired problems to resolve small differences:

| Configuration | LLM calls | Pass rate |
|---|---|---|
| One-shot, single sample | 1.0 | 57.6% |
| One-shot, best of 5 samples | 5.0 | 57.9% |
| Single-agent execution-retry | 1.5 | 81.7% |
| Full multi-agent | 5.3 | 80.5% |

Execution feedback is worth about 24 points. Adding five more agents on top of
it is worth `-1.2` points (95% CI `[-7.3, +4.9]`, exact Wilcoxon p = 0.76) at
roughly 3.6x the model calls. Drawing five independent samples instead, at five
times the call budget, is worth 0.4 points, so the gain comes from feedback
rather than from extra sampling.

The negative result is the more reliable half. Both retry conditions see stderr
from the tests that also grade them, which inflates any comparison against
one-shot, but it affects multi-agent and single-retry equally and so leaves the
comparison between those two clean.

## Requirements

| | |
|---|---|
| Python | 3.11 (3.11.7 used for all reported runs) |
| OS | Windows 11 for the reported runs; Linux and macOS supported |
| GPU | NVIDIA RTX 4050 Laptop, 6 GB VRAM, for the reported runs |
| CPU / RAM | Intel i5-13420H, 16 GB DDR5 |
| Model backend | Ollama, all models open weight and run locally |
| Disk | about 25 GB for the model set, 10 MB for this repository |

No paid API is used anywhere. The full grid reproduces at zero marginal cost.

## Installation

```bash
git clone https://github.com/rohithreddybc/execuGraph.git
cd execuGraph
pip install -e .
```

Install Ollama from https://ollama.com/download, then pull the models:

```bash
ollama pull qwen2.5-coder:7b-instruct-q4_K_M          # primary backbone
ollama pull deepseek-coder-v2:16b-lite-instruct-q4_K_M # cross-model condition
ollama pull qwen3-coder:30b-a3b-q4_K_M                 # supplementary condition
```

Exact model tags and digests are recorded in `REPRODUCIBILITY.md` and in each
run's `run_meta.json`.

## Verifying the installation

```bash
pytest -q tests/unit          # 44 tests, no model required, about 40 s
ruff check execugraph scripts tests
```

The unit suite includes a reference-solution control: known-good programs that
must pass the sandbox, and escape attempts that must fail. If the sandbox ever
regresses, that test fails rather than a results table quietly changing.

## Reproducing the paper without re-running the models

Every number in the paper is produced from the trial logs in `results/` by one
script. Nothing is entered by hand.

```bash
python scripts/build_all_tables.py \
    --results results/grid-main-rescored \
              results/grid-followup-rescored \
    --out generated_tables
```

This takes a few seconds and writes one `.tex` fragment per table plus
`all_numbers.json`, a machine-readable dump of every reported quantity. Running
it twice produces byte-identical output. `all_numbers.json` is what the prose in
the paper was checked against.

## Re-running the experiments

```bash
# full primary grid
RUN_ID=grid-main ./scripts/run_full_grid.sh

# the follow-up conditions (external single-retry, budget 1, N=5 ablations)
python scripts/run_remaining_experiments.py
```

The complete grid is 3,260 trials and takes roughly 30 to 45 hours on the
hardware above. `scripts/run_remaining_experiments.py` is idempotent: it skips
any stage that already has a `run_summary.json`, so an interrupted run resumes
rather than restarting. `REPRODUCIBILITY.md` has the per-condition commands,
seeds, and expected runtimes.

## Repository layout

```
execugraph/
  agents/          the six agents, one module each
  graph/           LangGraph workflow definition and routing predicate
  execution/       subprocess sandbox and code sanitiser
  benchmarks/      internal-30, HumanEval, APPS, MBPP loaders
  llm/             provider-agnostic backend (Ollama, HuggingFace fallback)
  analysis/        statistics
  runner/          trial and batch runners, CLI
configs/           one YAML per experimental condition
results/           per-trial JSONL logs behind every reported number
generated_tables/  every results table, regenerated from those logs
scripts/           experiment driver, re-scoring tool, table generator
tests/             44 unit tests plus integration smoke tests
dataset/           the curated 30-problem benchmark as JSONL
```

### Results directories

| Directory | Contents |
|---|---|
| `grid-main` | primary grid as originally executed |
| `grid-main-rescored` | the same trials re-scored through the corrected sandbox |
| `grid-followup` | external single-retry, budget 1, N=5 ablations, sampling control |
| `grid-followup-rescored` | as above, re-scored |
| `example_run` | small synthetic artifact for exercising the pipeline; not real results |
| `smoke*`, `aux-*` | development smoke runs, not cited in the paper |

The paper reports the two `-rescored` trees. Each run directory holds
`trials.jsonl` (one JSON object per trial, including the generated program),
`run_meta.json` (host, config, model), and `run_summary.json`.

## Benchmarks

- **Internal-30**: 30 data structures and algorithms problems, 10 each of
  dynamic programming, graph algorithms, and data structures. Each carries a
  documented selection rationale, a target signature with accepted aliases, and
  deterministic tests. Defined in `execugraph/benchmarks/internal30.py`, exported
  to `dataset/internal30.jsonl`.
- **HumanEval**: all 164 problems, official tests, run verbatim in the sandbox.
- **APPS-introductory**: 50-problem subset, uniform random sample, seed 42.

## A note on the sandbox

The sandbox decides the dependent variable, so a defect in it does not merely
weaken isolation, it corrupts the results.

The original import policy gated `__import__` against a flat allow-list. That
looks reasonable and is wrong: importing an allow-listed pure-Python module
pulls in its private C accelerator, so `bisect` imports `_bisect`, `heapq`
imports `_heapq`, and `io` imports `_io`. None of those roots were on the list,
so the import was refused and a textbook-correct program was recorded as a
sandbox violation. It affected 135 of 1,335 trials, and it affected conditions
unevenly, because a condition that emits more candidate programs has more
chances to trip it.

The corrected policy pre-imports the allow-listed modules before installing the
guard, then admits anything already loaded while refusing an explicit deny-list.
Because every trial record stores the program it produced, correcting the
results required no new generation:

```bash
python scripts/rescore_trials.py \
    --in  results/grid-main \
    --out results/grid-main-rescored
```

That replays the stored artifacts through the corrected sandbox on CPU in a few
minutes. No model is invoked, so the programs are exactly those the original
runs produced and only the scoring changes.

The sandbox is a restricted CPython subprocess, not a container. It is adequate
for running code a model produced while trying to solve a stated problem, and
not adequate against code written to escape. Deployment in an adversarial
setting needs OS-level isolation.

## Licence and citation

Apache-2.0, see `LICENSE`. Citation metadata is in `CITATION.cff`.

## Contact

Open an issue on this repository, or contact the corresponding author listed in
the paper.
