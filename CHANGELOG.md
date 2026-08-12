# Changelog

## Matched-compute sampling control + referee-driven revision (2026-08-11, later)

### New experiment: the control two referees asked for
`e2_he_so_bo5` -- one-shot at N=5 on all 164 HumanEval problems (820 trials),
filtered through the same sandbox. Best-of-5 accepts a problem if any of the
five samples passes, at ~5x the call budget of pass@1.

| Configuration | LLM calls | Pass % |
|---|---|---|
| One-shot, single sample | 1.0 | 57.6 |
| One-shot, best of 5 | 5.0 | 57.9 |
| Single-retry | 1.5 | 81.7 |
| Multi-full | 5.3 | 80.5 |

Five samples buy +0.4 pp; execution feedback buys +24.1 pp at under a third of
the calls. On 161 of 164 problems all five samples agree, because the Generator
decodes at temperature 0.0 -- repeated sampling reproduces the same program.
The gain is feedback, not extra lottery tickets. Scope stated honestly in the
paper: temperature 0.0 makes this a weak sampling baseline by construction.

### Manuscript, after two independent referee reviews
Roughly 60 fixes. The substantive ones:

- A **fabricated pass-rate** (`lis` 40.0% MF) that anchored a whole mechanistic
  subsection; the table says 100/100/100. Section re-derived.
- Holm-adjusted p-values in Section 4.7 were pre-revision (0.249/0.624/0.624 ->
  0.375/0.375/0.547), contradicting the paper's own table.
- The RAG ablation paragraph quoted superseded N=2 numbers.
- Cross-model N reported as 4; it is 2. "Eight trial flips" -> four.
- Five wrong cost ratios, including "sub-linear token scaling" which is in fact
  super-linear (11.9x tokens on 5.3x calls).
- Section 6.3 recommended multi-full for DeepSeek on grounds its own table
  refutes (MF 83.3 = SO 83.3, below SR 86.7).
- Abstract cut 378 -> ~245 words; retitled to state the finding.
- Declarations block added (Springer requirement; its absence blocks at
  editorial screening). Funding, competing interests, CRediT, data availability.
- Sandbox-correction section moved out of the Results lead and reframed as
  harness validation rather than confession.
- Limitations grouped from thirteen items into five themes.
- Notation: unused delta in the transition tuple, MAX/B retry-cap mismatch,
  "acyclic" claim on a graph with a retry back-edge.
- Two figures were never cited in text.
- Added Olausson et al. (self-repair vs sampling) and Kapoor et al. (agent
  evaluation without cost-matched baselines) -- both verified.

### Verification
43 pp, 0 LaTeX errors, 0 undefined references, 44 references. 44 unit tests,
ruff clean, table regeneration byte-identical, all 32 hard-coded TikZ figure
values checked against `all_numbers.json`. 3,260 trials across 28 runs.

## Follow-up experiment grid (2026-08-11)

Closes the gap the sandbox-correction pass could not: single-retry, the
configuration the paper recommends, had never been run on any external
benchmark or on the second backbone. 1,262 new trials, ~10.5 h unattended.

### Added runs
- `e2_he_sr`, `e2_he_so_164`, `e2_he_mf_164` - all three conditions on the
  FULL 164-problem HumanEval suite. Earlier work used problems 0-63 and
  described the subset as index-stratified with seed 42; it was simply the
  first 64 in benchmark order. Running the full suite removes the sampling
  step, the incorrect description, and the reference to a manifest file
  (`benchmarks/humaneval_64.json`) that never existed.
- `e3_apps_sr`, `e7_xm_sr` - single-retry on APPS-introductory and DeepSeek.
- `e5_rb1` - retry budget 1, giving the sweep an interior point.
- `e4_*_n5` - all four ablations re-run at N=5 to match the headline baseline.

### Headline result
HumanEval at n=164 is the only adequately powered comparison in the study:

| Contrast | delta | 95% CI | exact p | Holm p |
|---|---|---|---|---|
| SR - SO | +25.6 pp | [+18.9, +32.3] | <0.0001 | <0.0001 |
| MF - SO | +24.4 pp | [+15.2, +32.9] | <0.0001 | <0.0001 |
| MF - SR | -1.2 pp  | [-7.3, +4.9]   | 0.762   | 0.762   |

Execution feedback accounts for the gain; multi-agent decomposition adds
nothing measurable on top of it at ~5x the LLM calls. The MF-SR contrast is
the only powered comparison free of the test-visibility confound, since both
conditions retry against the same tests.

### Negative controls, and an unplanned finding
`-Reviewer`, `-Optimizer` and `+RAG` cannot alter acceptance by construction,
so at N=5 they are replications of multi-full. All three returned exactly
78.7% (118/150) while differing at the level of individual trials and
generated programs, putting the within-session aggregate noise floor near
zero. The May baseline sits 3.3 pp higher and shares byte-identical code on
only 56/150 trials, so cross-session model-server drift exceeds within-session
noise. Against the replication level, `-Planner` gains +8.0 pp - stronger than
the earlier N=2 ablations implied - though the per-problem paired test remains
inconclusive at 6 discordant problems (exact p = 0.156). Both are reported.

The retry sweep is non-monotonic (76.7 / 71.7 / 83.3). Since a larger budget
can only add regeneration attempts to a failing trial, the dip is a direct
display of run-to-run variance at N=2 and is reported as such.

### Tooling
- `scripts/run_remaining_experiments.py` - idempotent unattended driver.
- `scripts/build_all_tables.py` - now reads several results trees, emits
  Table 15 (HumanEval paired stats), and records the replication analysis in
  `all_numbers.json`. Regeneration verified byte-identical.
- Fixed an unescaped `%` in generated table headers that silently commented
  out the end of each header row.
- Table 1 rewritten with wrapping columns; it had been overfull by 148 pt with
  the acceptance-predicate column running off the page. Added MapCoder and
  Self-Debug rows.

Totals: 2,440 trials across 27 runs, all deterministic-tested. 44 unit tests,
ruff clean, LaTeX builds with 0 errors and 0 undefined references.

## Sandbox correction and re-scoring (post-DSM review)

### Fixed, execution sandbox

The import guard gated `__import__` against a flat allow-list. Importing an
allow-listed pure-Python module transitively imports its private C accelerator
(`bisect` -> `_bisect`, `heapq` -> `_heapq`, `io` -> `_io`), whose root is not
on the list, so the import was refused and the trial was recorded as
`sandbox_violation`. Correct programs were scored as failures: 135 of 1,335
records (10.1%) in the original grid, at rates that differed by condition.

The corrected child pre-imports allow-listed modules before installing the
guard, then admits any import whose root is allow-listed or already loaded and
refuses an explicit deny-list unconditionally (`random` pulls `os`, so
transitive loading alone cannot be the criterion).

Also fixed, all verified by test:

- `subprocess.run` now passes an explicit minimal `env=`; previously the child
  inherited the parent environment, so generated code could read `HF_TOKEN`.
- `sys` and `io` are served as restricted shims. The real modules expose
  `sys.modules` (reachable route to `os`) and `io.open` (which is
  `builtins.open` under another name, and did write files).
- `resource.setrlimit(RLIMIT_AS, 1 GiB)` is applied where available. It is
  unavailable on Windows; the code degrades gracefully and the paper now states
  the platform caveat instead of claiming the ceiling.
- `input` is retained (it reads only the harness-supplied stdin buffer);
  deleting it failed every stdin-driven APPS candidate for no isolation gain.
- Removed 47 lines of dead `_CHILD_PRELUDE` containing non-functional
  placeholder logic and a comment describing behaviour that never happened.

### Added

- `scripts/rescore_trials.py`, replays every stored candidate program through
  the corrected sandbox using the same Evaluator entry point. No LLM is
  invoked; trial records persist the generated code, so the grid needed
  re-scoring rather than re-running. Applies one deduplication rule
  (last-wins per `(problem_id, trial)`) uniformly, replacing three
  inconsistent conventions; 157 duplicate rows from resumed runs are dropped,
  leaving 1,178 distinct trials.
- `scripts/build_all_tables.py`, emits all twelve result tables plus
  `all_numbers.json`. The previous generator covered only tab3-tab6 and left
  the rest as `	odo{}` stubs, so five tables in earlier drafts had no
  traceable source. Statistics corrected: exact Wilcoxon rather than the normal
  approximation (invalid at four discordant pairs, where it reported p=0.083
  against an exact 0.125), cluster bootstrap over problems, Holm-Bonferroni
  across the three pooled contrasts.
- `tests/unit/test_sandbox.py`, reference-solution control. Known-correct
  programs using `bisect`, `heapq`, `collections`, `functools`, `itertools`,
  and `re` must pass; escapes (env leak, `sys.modules` route to `os`,
  `io.open` write) must fail. This is the test whose absence let the original
  defect ship. 34 -> 44 unit tests.

### Result

Pass-rates after re-scoring (original -> corrected): internal-30 SO
73.3 -> 77.3, SR 83.3 -> 90.0, MF 76.7 -> 82.0; HumanEval SO 54.7 -> 56.2,
MF 57.8 -> 85.9; APPS-intro SO 6.0 -> 20.0, MF 10.0 -> 22.0. `dijkstra` moved
from 0% in every condition to 100%, it had been failing on its `heapq`
import, not on the model. Pre-correction fragments are retained under
`generated_tables_ORIGINAL_pre_correction/` so the correction is auditable.

 (code)

All code-side changes for the IEEE Access revision are listed here.
The paper-side change log lives at `paper/CHANGELOG.md`.
The overall summary is at `../CHANGELOG_overall.md`.

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

## 0.2.0, IEEE Access revision

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
- `scripts/run_full_grid.sh`, one-shot driver for the full IEEE Access grid (~30 to 45 h on RTX 4050).
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
