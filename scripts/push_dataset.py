"""Regenerate and publish the internal-30 dataset to a HuggingFace dataset repo.

Identity-neutral: pass the target repo id on the command line so the same script
can keep multiple mirrors in sync (e.g. an anonymized review copy and a named
release copy). Authenticate first with ``huggingface-cli login`` (or set
``HF_TOKEN``) using the token of the account that owns ``--repo-id``.

Examples::

    # anonymized review mirror
    python scripts/push_dataset.py --repo-id Rohithreddybc/llm-code-generation-benchmark \
        --card dataset/README_anon.md

    # named release mirror
    python scripts/push_dataset.py --repo-id <user>/execugraph-internal30 \
        --card dataset/README.md

Run it once per mirror to keep them updated; the data file is always regenerated
from ``execugraph/benchmarks/internal30.py`` so the mirrors never drift.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True, help="HF dataset repo, e.g. user/execugraph-internal30")
    ap.add_argument("--card", type=Path, default=None, help="Optional README.md dataset card to upload")
    ap.add_argument("--private", action="store_true", help="Create the repo as private")
    args = ap.parse_args(argv)

    work = Path("dataset")
    work.mkdir(exist_ok=True)
    data_file = work / "internal30.jsonl"

    # 1. regenerate the data from the single source of truth
    subprocess.run(
        [sys.executable, "scripts/export_dataset.py", "--out", str(data_file)],
        check=True,
    )

    # 2. upload to the dataset repo
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo_id=args.repo_id, repo_type="dataset", private=args.private, exist_ok=True)
    api.upload_file(
        path_or_fileobj=str(data_file),
        path_in_repo="internal30.jsonl",
        repo_id=args.repo_id,
        repo_type="dataset",
    )
    if args.card and args.card.exists():
        api.upload_file(
            path_or_fileobj=str(args.card),
            path_in_repo="README.md",
            repo_id=args.repo_id,
            repo_type="dataset",
        )
    print(f"published internal-30 to https://huggingface.co/datasets/{args.repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
