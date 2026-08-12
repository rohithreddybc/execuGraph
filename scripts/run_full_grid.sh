#!/usr/bin/env bash
# Optimised full experiment grid for the IEEE Access submission.
#
# Tuned for an RTX 4050 Laptop GPU (6 GB VRAM, 16 GB RAM):
#   - Single-backbone configs (default.yaml, crossmodel.yaml) keep one
#     model hot in VRAM; no swap overhead.
#   - Trimmed scope on phases that contributed little marginal value:
#       * E5 retry sweep: {0,1,2,3} -> {0,2}        (saves ~50%)
#       * E4 ablations:   N=3      -> N=2          (saves ~33%)
#       * E2 HumanEval:   164      -> 64 problems  (saves ~60%)
#       * E3 APPS:                    50           (unchanged; already small)
#       * E7 cross-model: N=3      -> N=2          (saves ~33%)
#   - OLLAMA_KEEP_ALIVE=30m so the model never unloads between calls.
#
# Estimated wall-clock on RTX 4050: ~6-9 hours total (was ~30-45 h).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ID="${RUN_ID:-grid-$(date +%Y%m%d-%H%M%S)}"
OUT="$ROOT/results/$RUN_ID"
CFG="${CFG:-$ROOT/configs/default.yaml}"

# Keep the loaded model hot for the duration of the grid.
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-30m}"

echo "=== run id: $RUN_ID ==="
echo "    config: $CFG"
echo "    keep-alive: $OLLAMA_KEEP_ALIVE"
echo ""

# E1. Internal-30 x {SO, SR, MF}, 5 trials, retry=2. Headline numbers.
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e1_so" --condition single-oneshot --n-trials 5
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e1_sr" --condition single-retry  --n-trials 5 --retry-budget 2
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e1_mf" --condition multi-full    --n-trials 5 --retry-budget 2

# E4. Per-agent ablations on internal-30, N=2 trials.
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e4_no_planner"   --condition multi-no-planner   --n-trials 2 --retry-budget 2
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e4_no_reviewer"  --condition multi-no-reviewer  --n-trials 2 --retry-budget 2
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e4_no_optimizer" --condition multi-no-optimizer --n-trials 2 --retry-budget 2
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e4_rag_on"       --condition rag-on             --n-trials 2 --retry-budget 2

# E5. Retry-budget sweep, trimmed to {0, 2}. multi-full, N=2.
for rb in 0 2; do
  python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e5_rb$rb" --condition multi-full --n-trials 2 --retry-budget "$rb"
done

# E2. HumanEval external-validity anchor (64-problem subset, N=1).
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e2_he_so" --benchmark humaneval --condition single-oneshot --n-trials 1 --limit 64
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e2_he_mf" --benchmark humaneval --condition multi-full     --n-trials 1 --retry-budget 2 --limit 64

# E3. APPS-introductory subset (50 problems already, N=1).
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e3_apps_so" --benchmark apps_intro --condition single-oneshot --n-trials 1
python -m execugraph.runner.cli --config "$CFG" --output "$OUT/e3_apps_mf" --benchmark apps_intro --condition multi-full     --n-trials 1 --retry-budget 2

# E7. Cross-model: GPT-OSS-20B (N=2; single-backbone via configs/crossmodel.yaml).
if [[ "${RUN_CROSSMODEL:-1}" == "1" ]]; then
  python -m execugraph.runner.cli --config "$ROOT/configs/crossmodel.yaml" --output "$OUT/e7_xm_so" --condition single-oneshot --n-trials 2
  python -m execugraph.runner.cli --config "$ROOT/configs/crossmodel.yaml" --output "$OUT/e7_xm_mf" --condition multi-full     --n-trials 2 --retry-budget 2
fi

# E9. Latest-2026 supplementary: Qwen3-Coder-30B-A3B-Instruct on 10-problem
# subset of internal-30. Demonstrates the framework's gains hold on the
# May 2026 strongest open-weight code model that fits the reference
# hardware. Sample is small because Qwen3-Coder:30b runs ~270 s per
# multi-full trial via RAM offload on 6 GB VRAM.
if [[ "${RUN_LATEST_2026:-1}" == "1" ]]; then
  python -m execugraph.runner.cli --config "$ROOT/configs/latest2026.yaml" --output "$OUT/e9_l26_so" --benchmark internal30 --condition single-oneshot --n-trials 1 --limit 10
  python -m execugraph.runner.cli --config "$ROOT/configs/latest2026.yaml" --output "$OUT/e9_l26_mf" --benchmark internal30 --condition multi-full     --n-trials 1 --retry-budget 2 --limit 10
fi

# Build paper tables and figures.
python -m execugraph.analysis.build_tables  "$OUT" --out "$ROOT/../paper/tables"
python -m execugraph.analysis.build_figures "$OUT" --out "$ROOT/../paper/figures"
echo "=== grid complete: $OUT ==="
