"""Seed the ChromaDB technique store with the 69 algorithmic techniques
defined in :mod:`execugraph.memory.TECHNIQUES`.

Run once before enabling the RAG ablation row::

    python -m execugraph.memory.seed_techniques

The store is persisted to ``./memory/techniques_db`` (relative to where
you run from) and re-running the script is idempotent.
"""

from __future__ import annotations

from pathlib import Path

from .TECHNIQUES import TECHNIQUES


def _format_document(t: dict) -> str:
    return (
        f"Technique: {t.get('name','')}\n"
        f"When to use: {t.get('when_to_use','')}\n"
        f"Core idea: {t.get('core_idea','')}\n"
        f"Time: {t.get('time','')}\n"
        f"Space: {t.get('space','')}\n"
        f"Common mistakes: {t.get('mistakes','')}"
    )


def seed(persist_dir: str = "./memory/techniques_db", collection: str = "dsa_techniques") -> int:
    try:
        import chromadb  # type: ignore
        from chromadb.utils import embedding_functions  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "Seeding requires chromadb. Run `pip install chromadb`."
        ) from e

    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    coll = client.get_or_create_collection(name=collection, embedding_function=ef)

    docs, ids, metas = [], [], []
    for i, t in enumerate(TECHNIQUES):
        docs.append(_format_document(t))
        ids.append(f"tech-{i:03d}")
        metas.append({"name": t.get("name", ""), "domain": "DSA", "type": "algorithmic-technique"})

    coll.upsert(ids=ids, documents=docs, metadatas=metas)
    print(f"[seed_techniques] upserted {len(docs)} techniques into '{collection}' at {persist_dir}")
    return len(docs)


if __name__ == "__main__":  # pragma: no cover
    seed()
