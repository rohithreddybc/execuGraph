"""Optional ChromaDB-backed retrieval layer for the Planner.

This is a thin wrapper that is import-safe even when ``chromadb`` is not
installed; in that case ``TechniqueRetriever`` returns the empty list
when queried.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TechniqueRetriever:
    persist_dir: str = "./memory/techniques_db"
    collection: str = "dsa_techniques"
    top_k: int = 5
    embedding_model: str = "all-MiniLM-L6-v2"

    def __post_init__(self) -> None:
        try:
            import chromadb  # type: ignore
            from chromadb.utils import embedding_functions  # type: ignore

            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
            try:
                self._coll = self._client.get_collection(
                    name=self.collection, embedding_function=self._ef
                )
            except Exception:
                self._coll = None
        except Exception:
            self._coll = None

    def retrieve(self, query: str) -> list[str]:
        if self._coll is None:
            return []
        try:
            res = self._coll.query(query_texts=[query], n_results=self.top_k)
            docs = res.get("documents") or [[]]
            return list(docs[0])
        except Exception:
            return []
