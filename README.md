# ExecuGraph

Code and data for the paper *Execution Feedback, Not Role Decomposition: A
Controlled Comparison of Single- and Multi-Agent LLM Code Synthesis*.

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

## What we found

On the full 164-problem HumanEval suite, which is the only benchmark here with
enough paired problems to resolve small differences:

| Configuration | LLM calls | Pass rate |
|---|---|---|
| One-shot, single sample | 1.0 | 57.6% |
| One-shot, best of 5 samples | 5.0 | 57.9% |
| Single-agent execution-retry | 1.5 | 81.7% |
| Full multi-agent | 5.3 | 80.5% |

Execution feedback is worth about 24 points. Adding five more agents on top of
it is worth `-1.2` points (95% CI `[-7.3, +4.9]`, exact Wilcoxon p = 0.76) at
roughly 3.6x the model calls. Drawing five independent samples instead, at five
times the call budget, is worth 0.4 points, so the gain is feedback rather than
extra sampling.

The negative result is the more reliable half. Both retry conditions see stderr
from the tests that also grade them, which inflates any comparison against
one-shot, but affects multi-agent and single-retry equally and so leaves the
comparison between those two clean.

## Quick start

```bash
pip install -e .

# Local model backend. Install Ollama from https://ollama.com/download, then:
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Check the harness without touching a model
pytest -q tests/unit

# Small run: 3 problems, 1 trial
python -m execugraph.runner.cli \
    --config configs/default.yaml \
    --output results/smoke \
    --condition multi-full \
    --n-trials 1 --limit 3
```

## Reproducing the paper

Every number in the paper comes from the logs in `results/` by way of one
script. Nothing is typed in by hand.

```bash
python scripts/build_all_tables.py \
    --results results/submission-20260509-223437-rescored \
              results/submission-20260811-followup-rescored \
    --out generated_tables
```

That writes one `.tex` fragment per table plus `all_numbers.json`, which is the
machine-readable version used to check the prose. Running it twice gives byte
identical output.

To re-run experiments from scratch, see `REPRODUCIBILITY.md`. The full grid is
3,260 trials and takes roughly 30 to 45 hours on an RTX 4050 with 6 GB of VRAM.
Every model is open weight and runs locally, so it costs nothing in API fees.

## A note on the sandbox

The sandbox is load bearing: it decides the dependent variable, so a bug in it
does not just weaken isolation, it corrupts the results.

The original import policy gated `__import__` against a flat allow-list. That
looks reasonable and is wrong, because importing an allow-listed pure-Python
module pulls in its private C accelerator: `bisect` imports `_bisect`, `heapq`
imports `_heapq`, `io` imports `_io`. None of those roots were on the list, so
the import failed and a textbook-correct program was recorded as a sandbox
violation. It hit 135 of 1,335 trials, and it hit conditions unevenly, because
a condition that emits more candidate programs has more chances to trip it.

The fix pre-imports the allow-listed modules before installing the guard, then
admits anything already loaded while refusing an explicit deny-list. Since every
trial record stores the program it produced, correcting the results needed no
new generation:

```bash
python scripts/rescore_trials.py \
    --in  results/submission-20260509-223437 \
    --out results/submission-20260509-223437-rescored
```

That replays stored artifacts through the corrected sandbox on CPU in a few
minutes. No model is invoked, so the programs are exactly the ones the original
runs produced and only the scoring changes.

`tests/unit/test_sandbox.py` now includes a reference-solution control: known
good programs that must pass, plus escapes that must fail. That test is what
was missing, and it is why the original defect shipped.

## Layout

```
execugraph/        framework: agents, workflow, sandbox, benchmarks, analysis
configs/           one YAML per experimental condition
results/           per-trial JSONL logs behind every reported number
generated_tables/  result tables, regenerated from those logs
scripts/           experiment driver, re-scoring tool, table generator
tests/             44 unit tests plus integration smoke tests
dataset/           the curated 30-problem benchmark as JSONL
```

## Benchmarks

- **Internal-30**: 30 data structures and algorithms problems, 10 each of
  dynamic programming, graph algorithms, and data structures, with a documented
  selection rationale and deterministic tests. Defined in
  `execugraph/benchmarks/internal30.py` and exported to `dataset/`.
- **HumanEval**: all 164 problems, official tests, run verbatim in the sandbox.
- **APPS-introductory**: a 50-problem subset, seed 42.

## Citation

See `CITATION.cff`.

## Licence

Apache-2.0.
