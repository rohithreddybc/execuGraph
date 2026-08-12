# Synthetic example artifact — DO NOT cite in the paper

This directory contains a `trials.jsonl` produced by a deterministic
random generator for the sole purpose of exercising
`execugraph/analysis/build_tables.py` without running an LLM.

**These numbers are not real experimental results.** The paper's
`paper/tables/*.tex` fragments remain TODO placeholders until they are
regenerated from a real run produced by `scripts/run_full_grid.sh`.

The script that produced this file is shown below for full transparency:

```python
import json, random
random.seed(0)
# ...see _repo_clone/results/example_run/regen_synthetic.py
```
