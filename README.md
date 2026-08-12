# ExecuGraph

A multi-agent, execution-grounded framework for backend code synthesis with Large Language Models.

> ExecuGraph decomposes code generation into specialized agents (Planner, Code Generator, Logical Reviewer, Evaluator, Optimizer, Explainer) coordinated by a deterministic LangGraph workflow over typed shared state. **Acceptance is decided by sandboxed execution, not by static review.** A bounded retry loop drives recovery from runtime failures.

This repository accompanies the paper *ExecuGraph: A Multi-Agent, Execution-Grounded Framework for Reliable Backend Code Synthesis with Large Language Models* (IEEE Access submission).

---

## Quick start

```bash
# 1. Python deps
pip install -e .

# 2. Local LLM backend (default; recommended)
#    Install Ollama from https://ollama.com/download, then:
ollama pull qwen3:4b-instruct-2507-q4_K_M       # planner / reviewer / explainer
ollama pull qwen2.5-coder:7b-instruct-q4_K_M    # generator / optimizer

# 3. Smoke test the harness without running an LLM
pytest -q tests/unit

# 4. Run a small experiment (3 problems, 1 trial)
python scripts/run_experiment.py \
    --config configs/default.yaml \
    --output results/smoke \
    --condition multi-full \
    --n-trials 1 --limit 3
```

For the full IEEE Access experiment grid (~30–45 hours on an RTX 4050 6 GB):

```bash
RUN_ID=submission ./scripts/run_full_grid.sh
python -m execugraph.analysis.build_tables  results/submission --out ../paper/tables
python -m execugraph.analysis.build_figures results/submission --out ../paper/figures
```

To preview what the paper looks like *before* running the grid (using
synthetic data, with a DRAFT watermark):

```bash
./scripts/build_preview.sh        # produces ../paper_preview/main.pdf
```

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the full per-experiment runtime estimates and exact commands.

---

## Architecture

```
                 ┌────────────┐
                 │  Planner   │◄──── (optional) ChromaDB technique store
                 └──────┬─────┘
                        │ structured plan
                        ▼
                 ┌────────────┐                ┌──────────────────┐
        ┌────────│ Generator  │───────────────►│ Logical Reviewer │  (advisory)
        │        └──────┬─────┘                └─────────┬────────┘
        │ retry         │ candidate code                 │ structured advisory
        │ feedback      ▼                                ▼
        │       ┌──────────────────────┐
        │       │     Evaluator        │ ◄── deterministic OR LLM-generated tests
        │       │  subprocess sandbox  │ ◄── runtime acceptance signal
        │       └────────┬─────────────┘
        │                │
        ▼                ▼
   fail / budget   pass
        │                │
        │                ▼
        │         ┌────────────┐
        │         │ Optimizer  │  (re-validates before accepting)
        │         └─────┬──────┘
        │               ▼
        │         ┌────────────┐
        └────────►│ Explainer  │
                  └────────────┘
```

The same graph reduces by configuration to **single-oneshot** (Generator + Evaluator only, retry budget 0) and **single-with-retry** (a Reflexion-style baseline). This makes per-component contributions measurable in isolation.

---

## Repository layout

```
.
├── execugraph/              # the package
│   ├── agents/              # Planner, Generator, Reviewer, Evaluator, Optimizer, Explainer
│   ├── graph/               # LangGraph workflow + standalone routing predicate
│   ├── benchmarks/          # internal30, APPS-introductory, HumanEval loaders
│   ├── execution/           # subprocess sandbox + code sanitisation
│   ├── llm/                 # provider-agnostic LLM backends (Ollama, HF)
│   ├── memory/              # optional ChromaDB technique store
│   ├── pipelines/           # single-oneshot, single-with-retry, multi-agent
│   ├── runner/              # trial / batch / CLI runner
│   ├── analysis/            # paired Wilcoxon, McNemar, table generators
│   ├── prompts/             # prompt templates for each agent
│   └── ui/                  # Streamlit interactive demo
├── configs/                 # YAML configs per backend / model
├── tests/                   # pytest unit tests (no LLM needed)
├── scripts/                 # run_experiment.py, run_full_grid.sh
├── results/example_run/     # SYNTHETIC artifact for harness smoke testing
├── pyproject.toml
├── Dockerfile
└── REPRODUCIBILITY.md
```

The `Prompts/` directory at the top level (legacy) and the loose top-level `agents/`, `graph/`, `memory/`, `util/`, `app.py`, `test_*.py` files are **deprecated**: their behaviour was migrated into the `execugraph/` package and the `tests/` suite. They are retained for one release for backwards-compatibility readers, then will be deleted.

---

## Configuration

LLM backends are selected via YAML:

| File | Backend | Use case |
|-|-|-|
| `configs/default.yaml` | Qwen3-4B + Qwen2.5-Coder-7B (Ollama, q4) | Default; matches paper headline numbers |
| `configs/strong.yaml` | + Qwen3-Coder-30B-A3B MoE generator | Opt-in stronger generator (slower) |
| `configs/crossmodel.yaml` | Llama-3.1-8B + DeepSeek-Coder-V2-Lite-16B | Cross-model row (independent vendor family) |
| `configs/hf_fallback.yaml` | HuggingFace Inference API | No local GPU; rate-limited |

The selection is honoured by every entrypoint (`scripts/run_experiment.py`, `execugraph-run`, the Streamlit UI).

---

## Dataset

The curated **internal-30** benchmark (30 DSA problems, 125 deterministic test
cases) is the single source of truth for the paper's headline tables. It lives
in `execugraph/benchmarks/internal30.py` and is also published as a standalone
HuggingFace dataset for convenience:

- **HuggingFace:** <https://huggingface.co/datasets/anonymousreview111/execugraph-internal30>
- **Local copy:** [`dataset/internal30.jsonl`](dataset/internal30.jsonl) (regenerate with `python scripts/export_dataset.py`)

```python
from datasets import load_dataset
ds = load_dataset("anonymousreview111/execugraph-internal30", split="train")
```

To refresh the published dataset after editing the benchmark:

```bash
huggingface-cli login   # token of the dataset-owning account
python scripts/push_dataset.py \
    --repo-id anonymousreview111/execugraph-internal30 --card dataset/README.md
```

---

## Reproducing the paper tables

Every numeric cell in the paper traces to a JSON line in `results/<run>/trials.jsonl`. To regenerate:

```bash
RUN_ID=submission ./scripts/run_full_grid.sh
python -m execugraph.analysis.build_tables results/submission --out ../paper/tables
cd ../paper && latexmk -pdf main.tex
```

Cells in the paper that are currently `\todo{}` correspond to runs that have not yet been executed; running the grid above on the reference hardware will replace them automatically.

---

## Testing

```bash
pytest -q tests/unit          # 31 tests, no LLM required
ruff check execugraph tests   # lint
```

CI on GitHub Actions runs the lint + unit-test surface on every push.

---

## Authors

Author names and affiliations are withheld for double-blind review and will be
released on acceptance.

---

## Citing

This repository is an anonymized supplement for double-blind review. Citation
metadata will be released on acceptance.

---

## License

Apache-2.0.
