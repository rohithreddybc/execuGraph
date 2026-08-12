---
license: apache-2.0
language:
- en
tags:
- code-generation
- algorithms
- data-structures
- dynamic-programming
- graph-algorithms
- benchmark
- execution-grounded
pretty_name: ExecuGraph Internal-30 DSA Benchmark
size_categories:
- n<1K
configs:
- config_name: default
  data_files: internal30.jsonl
---

# ExecuGraph Internal-30 Benchmark

> **Anonymized for double-blind review.** Author, affiliation, and citation
> metadata are withheld and will be released on acceptance.

A curated suite of **30 data-structures-and-algorithms (DSA) problems** used as
the headline benchmark for the ExecuGraph framework. Each problem ships with an
unambiguous natural-language specification, the target function signature (and
accepted aliases), a documented selection rationale, and a set of
**deterministic test cases** (boundary, canonical, and stress).

## Composition

| Category | Problems | Notes |
|---|---|---|
| Dynamic Programming (`dp`) | 10 | Fibonacci, coin change, LCS, LIS, edit-distance-style recurrences |
| Graph Algorithms (`graph`) | 10 | BFS/DFS, topological sort, Dijkstra, Bellman, Ford, SCC, connectivity |
| Data Structures (`ds`) | 10 | LRU cache, min-stack, heap/priority queue, AVL, linked-list, traversal |

- 27 problems are originally designed; 3 are adapted from the
  APPS-introductory partition (marked `source = "apps-…"`).
- 30 problems, **125 deterministic test cases** in total.

## Fields

Each line in `internal30.jsonl` is one problem:

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable problem identifier (e.g. `topo_sort`) |
| `category` | string | `dp` \| `graph` \| `ds` |
| `source` | string | `internal` or `apps-<id>` |
| `difficulty` | string | `easy` \| `medium` \| `hard` |
| `statement` | string | Self-contained problem specification |
| `primary_function` | string | Expected function name |
| `signature_aliases` | list[string] | Accepted alternative function names |
| `selection_rationale` | string | Why the problem is included |
| `timeout_s` | float | Per-execution wall-clock budget |
| `tests` | list[object] | Test cases: `{args, expected, call, description, kind, has_custom_judge}` |

Within each test, **`args` and `expected` are JSON-encoded strings** (their
native types vary between int, list, bool, … across problems, so they are
serialized for a uniform, Arrow-loadable schema). Parse them back with
`json.loads`. A small number of graph problems whose correct output is not
uniquely ordered (e.g. topological sort) use a custom equality judge in the
reference harness; those tests are flagged with `has_custom_judge = true`. For
portable use, treat them as exact-match or supply an order-insensitive
comparison.

## Usage

```python
import json
from datasets import load_dataset

ds = load_dataset("anonymousreview111/execugraph-internal30", split="train")
p = ds[0]
print(p["id"], p["category"], len(p["tests"]))
args = json.loads(p["tests"][0]["args"])        # -> e.g. [10]
expected = json.loads(p["tests"][0]["expected"]) # -> e.g. 55
```

## Reproducibility

This dataset is regenerated from the framework's single source of truth
(`execugraph/benchmarks/internal30.py`) via `scripts/export_dataset.py` in the
accompanying (anonymized) code repository. Every numeric claim in the paper's
internal-30 tables is reproducible from that code together with this dataset.

## License

Released under the Apache-2.0 license.
