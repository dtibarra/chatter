"""Long-term memory backed by ChromaDB."""

from __future__ import annotations

import datetime
import json
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from chatter.config import settings


class MemoryStore:
    """Manages episodic and semantic memory via ChromaDB collections."""

    def __init__(self, path: str | None = None):
        db_path = path or str(settings.chromadb_path)
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.episodic = self.client.get_or_create_collection(
            name="episodic",
            metadata={"description": "Raw conversation events and experiences"},
        )
        self.semantic = self.client.get_or_create_collection(
            name="semantic",
            metadata={"description": "Extracted facts and knowledge"},
        )

    def store_episode(
        self,
        content: str,
        conversation_id: str,
        role: str = "user",
        metadata: dict | None = None,
    ) -> str:
        """Store a conversation event in episodic memory."""
        doc_id = str(uuid.uuid4())
        meta = {
            "conversation_id": conversation_id,
            "role": role,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        if metadata:
            meta.update(metadata)
        self.episodic.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[meta],
        )
        return doc_id

    def store_fact(
        self,
        fact: str,
        source: str = "extracted",
        metadata: dict | None = None,
    ) -> str:
        """Store a semantic fact in long-term memory."""
        doc_id = str(uuid.uuid4())
        meta = {
            "source": source,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        if metadata:
            meta.update(metadata)
        self.semantic.add(
            ids=[doc_id],
            documents=[fact],
            metadatas=[meta],
        )
        return doc_id

    def recall_episodes(
        self,
        query: str,
        n_results: int = 5,
        conversation_id: str | None = None,
    ) -> list[dict]:
        """Retrieve relevant episodic memories."""
        where = {"conversation_id": conversation_id} if conversation_id else None
        results = self.episodic.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )
        return self._format_results(results)

    def recall_facts(self, query: str, n_results: int = 5) -> list[dict]:
        """Retrieve relevant semantic facts."""
        results = self.semantic.query(
            query_texts=[query],
            n_results=n_results,
        )
        return self._format_results(results)

    def search_all(self, query: str, n_results: int = 5) -> dict:
        """Search both episodic and semantic memory."""
        return {
            "episodes": self.recall_episodes(query, n_results),
            "facts": self.recall_facts(query, n_results),
        }

    def list_facts(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all stored facts (for the web UI)."""
        results = self.semantic.get(limit=limit, offset=offset, include=["documents", "metadatas"])
        items = []
        for i, doc_id in enumerate(results["ids"]):
            items.append({
                "id": doc_id,
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        return items

    def list_episodes(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all stored episodes (for the web UI)."""
        results = self.episodic.get(limit=limit, offset=offset, include=["documents", "metadatas"])
        items = []
        for i, doc_id in enumerate(results["ids"]):
            items.append({
                "id": doc_id,
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        return items

    def delete_memory(self, collection: str, memory_id: str) -> bool:
        """Delete a specific memory by ID."""
        coll = self.episodic if collection == "episodic" else self.semantic
        coll.delete(ids=[memory_id])
        return True

    def get_stats(self) -> dict:
        """Get memory statistics."""
        return {
            "episodic_count": self.episodic.count(),
            "semantic_count": self.semantic.count(),
        }

    @staticmethod
    def _format_results(results: dict) -> list[dict]:
        items = []
        if not results["ids"] or not results["ids"][0]:
            return items
        for i, doc_id in enumerate(results["ids"][0]):
            items.append({
                "id": doc_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return items


# Singleton instance
memory_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    global memory_store
    if memory_store is None:
        memory_store = MemoryStore()
    return memory_store
