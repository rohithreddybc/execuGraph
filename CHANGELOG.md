# Changelog

## 0.4.0, sampling control and matched-N ablations

### Added
- **Matched-compute sampling control.** One-shot at N=5 on all 164 HumanEval
  problems, filtered through the same sandbox, giving a best-of-5 baseline at
  roughly the multi-agent call budget. Best-of-5 returns 57.9% against 57.6%
  for a single sample. On 161 of 164 problems all five samples agree, because
  the Generator decodes at temperature 0.0, so repeated sampling reproduces the
  same program. Additional compute alone does not reproduce the execution
  feedback effect.
- Single-retry extended to HumanEval, APPS-introductory, and the DeepSeek
  backbone, so every benchmark now covers all three primary conditions.
- HumanEval extended from a 64-problem subset to the full 164-problem suite for
  all conditions, which is what makes the paired analysis adequately powered.
- Retry budget 1, giving the sweep an interior point.
- All four ablations re-run at N=5 to match the headline baseline's trial count.
- `scripts/run_remaining_experiments.py`, an idempotent unattended driver.

### Changed
- `scripts/build_all_tables.py` reads several results trees, emits every table
  in the paper plus `all_numbers.json`, and records the replication analysis.
  Regeneration is byte-identical across runs.
- Results directories renamed from timestamps to descriptive names
  (`grid-main`, `grid-followup`, and their re-scored counterparts).

### Fixed
- Unescaped `%` in generated table headers, which silently commented out the
  remainder of each header row.

## 0.3.0, sandbox correction and re-scoring

### Fixed
- **Execution sandbox import policy.** The guard gated `__import__` against a
  flat allow-list, which refused allow-listed modules reached through their
  private C accelerators (`bisect` to `_bisect`, `heapq` to `_heapq`, `io` to
  `_io`) and recorded correct programs as sandbox violations. It affected 135 of
  1,335 trials and did so unevenly across conditions, since a condition that
  emits more candidate programs has more chances to trip it. The corrected
  policy pre-imports allow-listed modules before installing the guard, then
  admits anything already loaded while refusing an explicit deny-list.
- The child process inherited the parent environment, so generated code could
  read provider credentials. It now receives an explicitly constructed minimal
  environment.
- `sys` and `io` are served as restricted shims. The real modules expose
  `sys.modules`, which reaches any loaded module, and `io.open`, which is
  `open` under another name and could write files.
- `resource.setrlimit(RLIMIT_AS)` applied where available. It does not exist on
  Windows, so the platform caveat is documented rather than the guarantee.
- `input` retained: it reads only the harness-supplied stdin buffer, and
  removing it failed every stdin-driven candidate for no isolation benefit.
- Removed 47 lines of dead prelude code containing non-functional placeholders.

### Added
- `scripts/rescore_trials.py`, which replays stored candidate programs through
  the corrected sandbox using the same Evaluator path. No model is invoked,
  since every trial record persists the program it produced. Applies one
  deduplication rule (last wins per problem and trial) uniformly.
- Reference-solution control in `tests/unit/test_sandbox.py`: known-good
  programs that must pass, and escape attempts that must fail. Its absence is
  why the original defect went unnoticed. Unit tests 34 to 44.

## 0.2.3, Preview build, RAG seeded, Streamlit ported, more benchmarks, lint clean

### Added
- **`scripts/build_preview.sh`**, builds `paper_preview/main.pdf` from the synthetic example_run data with a red `DRAFT * synthetic data` watermark, so paper layout (page count, table widths, figure placement) can be inspected before running the real 30 to 45 h grid.
- **`execugraph/memory/TECHNIQUES.py`**, 69 algorithmic techniques (ported from legacy archive).
- **`execugraph/memory/seed_techniques.py`**, `python -m execugraph.memory.seed_techniques` seeds ChromaDB; idempotent. Required to run the RAG ablation row.
- **`tests/unit/test_techniques.py`**, sanity tests over the 69-technique catalogue (count, required fields, unique names).
- **`execugraph/ui/streamlit_app.py`**, clean port of the legacy Streamlit demo on the new package layout. Reads its backend from `EXECUGRAPH_CONFIG` (default `configs/default.yaml`); same agent code path as the CLI.
- **`execugraph/benchmarks/humaneval_plus.py`**, HumanEval+ loader (~80x stricter tests; addresses peer-review point W7 on contamination).
- **`execugraph/benchmarks/mbpp.py`**, MBPP-sanitized loader.
- **CLI `--benchmark`** now accepts `humaneval_plus` and `mbpp` in addition to `internal30 / humaneval / apps_intro`.
- **`CITATION.cff`** with all four authors.

### Changed
- `ruff check` is now clean across `execugraph/` and `tests/`. Test suite expanded to **38 passing** (was 35).

## 0.2.2, HumanEval / APPS loaders, figure generator, stub-LLM e2e tests

### Added
- **`execugraph/benchmarks/humaneval.py`**, loads the official 164-problem HumanEval test split via `datasets`, wraps each task's `check()` driver as a single sandboxed `TestCase`. The previously-claimed §IV.A external-validity row can now actually run.
- **`execugraph/benchmarks/apps_intro.py`**, loads a deterministic 50-problem random subset (seed=0) of APPS-introductory; converts the dataset's stdin/stdout pairs into sandboxed call-and-compare `TestCase`s.
- **`--benchmark {internal30, humaneval, apps_intro}` flag** on the runner CLI; `_load_problems()` resolves names. Default unchanged (internal30).
- **`execugraph/llm/stub_backend.py`**, deterministic stub LLM that picks a response based on substring predicates. Lets the workflow be exercised end-to-end without Ollama or HF credentials.
- **`tests/integration/test_smoke_pipeline.py`**, 4 pytest `@integration` tests that exercise `single_oneshot`, `single_with_retry`, `multi_agent` (full path), and a `multi_no_planner` ablation entirely against the stub backend. All pass.
- **`execugraph/analysis/build_figures.py`**, companion to `build_tables.py`. Emits 3 PDFs from the per-trial JSONL: category-level pass-rate bar chart, cost-vs-accuracy scatter, retry-convergence curve.
- **Three new figure references in the paper** (`fig:category_bar`, `fig:cost_accuracy`, `fig:retry_convergence`) using `\IfFileExists` so the paper compiles cleanly whether or not the figures have been generated yet (renders a `\todo{}` marker until they exist).
- **`scripts/run_full_grid.sh` extended** with E2 (HumanEval), E3 (APPS-introductory), and a final `build_figures` invocation alongside `build_tables`.

### Verified
- Total test suite now **35 passing** (31 unit + 4 integration).
- Paper still 10 pages, clean compile, no undefined references.

## 0.2.1, Model upgrade + JudgeSense integration

### Changed
- **Default backbone upgraded** to a cheaper-and-stronger pair: `qwen3:4b-instruct-2507-q4_K_M` for the non-code agents (Planner/Reviewer/Explainer) and `qwen2.5-coder:7b-instruct-q4_K_M` for the code agents (Generator/Optimizer). Qwen3-4B-Instruct (released July 2025, Apache-2.0) matches or beats the older Qwen2.5-7B-Instruct on instruction-following at half the size, freeing VRAM headroom and roughly halving non-code-agent latency.
- **Cross-model condition rewritten** to use an entirely independent vendor family: `llama3.1:8b-instruct-q4_K_M` + `deepseek-coder-v2:16b-lite-instruct-q4_K_M` (the 16B MoE with 2.4B active parameters). The previous DeepSeek-Coder-6.7B condition was a single-model swap inside the same architectural family; the new pair gives a stronger generalization signal.

### Added
- `configs/strong.yaml`, opt-in stronger generator: `qwen3-coder:30b-a3b-instruct-q4_K_M` (MoE, 3B active). Slower (RAM-spilling on 6 GB VRAM) but substantially better on harder DSA / APPS items.
- All open-weight, Apache-2.0 / Llama-3 community-licence models. **Zero paid-API cost** for the entire experimental grid.

## 0.2.0, major revision

### Added
- New `execugraph/` package replacing the loose top-level modules.
- `execugraph/llm/` provider-agnostic backend layer:
  - `OllamaBackend` (default, local) talks to `ollama serve` over HTTP and reports prompt / eval token counts.
  - `HFBackend` (fallback) for users without a GPU, behind `HUGGINGFACEHUB_API_TOKEN`.
  - `CostAccumulator` records tokens, wallclock, call counts for every per-trial JSON record.
- `execugraph/execution/sandbox.py`: subprocess-isolated execution with wall-clock timeout, restricted `__builtins__`, allow-listed imports. Replaces raw `exec()` / `eval()` in the prior evaluator.
- `execugraph/benchmarks/internal30.py`: 30 problems (10 DP + 10 graph + 10 DS, 27 internal + 3 APPS-introductory) with explicit selection rationales, signature aliases, and deterministic test cases. Single source of truth for paper Tables 3 to 5.
- `execugraph/pipelines/`:
  - `single_oneshot`, baseline 1.
  - `single_with_retry`, Reflexion-style baseline (peer-review W5).
  - `multi_agent`, full ExecuGraph.
- `execugraph/runner/` (trial / batch / CLI). Per-trial JSONL log captures problem, condition, model, seed, trial, retries used, error class, wallclock, tokens, calls, code, stderr (peer-review W3, W4, T5).
- `execugraph/analysis/`:
  - `stats.py`, paired Wilcoxon, McNemar, bootstrap CI (peer-review W8).
  - `build_tables.py`, emits LaTeX fragments the paper `\input{}`s.
- Per-agent ablation toggles wired through `GraphState.enable_*` flags (peer-review W4).
- Optimizer now re-evaluates before accepting (peer-review T1).
- Reviewer now emits structured JSON `{invariants, potential_failures, severity}` (peer-review Q4).
- `tests/unit/` pytest suite (31 tests) covering: sandbox safety, code sanitiser, problem loader integrity, evaluator behaviour incl. signature aliasing, cost tracker, workflow routing predicate, table-builder smoke. No LLM required to run.
- `.github/workflows/ci.yml`, ruff + unit tests on push/PR.
- `Dockerfile`, Python 3.11 base; recommends `--network=host` so the container reaches the host Ollama on `localhost:11434`.
- `REPRODUCIBILITY.md`, exact commands, hardware spec, model digests, runtime estimates per experiment.
- `scripts/run_full_grid.sh`, one-shot driver for the full experiment grid (~30 to 45 h on RTX 4050).
- `configs/{default,hf_fallback,deepseek}.yaml`, backend / model presets.
- `results/example_run/`, SYNTHETIC trial JSONL (clearly labelled) so the table-generation pipeline can be exercised offline.

### Changed
- `MAX_RETRIES` is no longer hardcoded; it is a per-run config field that the retry-budget sweep can vary across `{0, 1, 2, 3}` (peer-review T4).
- Reviewer is no longer source of truth; the workflow's decision predicate is purely execution-driven (formerly the reviewer could veto correct code).
- All prompt files moved into `execugraph/prompts/` and packaged via `package-data`.

### Deprecated (will be deleted in 0.3.0)
- Top-level `agents/`, `graph/`, `memory/`, `util/`, `app.py`, `test_*.py`, `Prompts/`. All functionality moved into the `execugraph/` package.

### Removed
- `agents/technique_selector_agent.py`, was never invoked.
- `memory/technique_selector.py`, was never invoked.
- `memory/vector_store.py`, superseded by `technique_store.py` and used wrong paths.
- ~470 lines of commented-out prior implementations in the old `app.py`.
- ~700 lines of commented-out prior implementations in the old `evaluator_agent.py`.

### Fixed
- Replaced raw `exec(code, {}, local_env)` / `eval(call, {}, local_env)` with subprocess-isolated sandbox calls (security + experimental hygiene).
- Probe used to resolve which signature alias is callable now uses `globals()` rather than `dir()` so functions defined at module scope are found reliably (regression caught by `tests/unit/test_evaluator.py`).
