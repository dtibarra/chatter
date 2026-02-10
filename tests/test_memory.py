"""Tests for the memory store."""

import pytest


def test_store_and_recall_fact(memory_store):
    memory_store.store_fact("User prefers dark mode", source="test")

    results = memory_store.recall_facts("dark mode preference")
    assert len(results) >= 1
    assert "dark mode" in results[0]["content"]


def test_store_and_recall_episode(memory_store):
    memory_store.store_episode(
        content="User asked about Python async patterns",
        conversation_id="conv-1",
        role="user",
    )

    results = memory_store.recall_episodes("async programming")
    assert len(results) >= 1
    assert "async" in results[0]["content"]


def test_recall_episodes_by_conversation(memory_store):
    memory_store.store_episode("Hello from conv 1", conversation_id="conv-1")
    memory_store.store_episode("Hello from conv 2", conversation_id="conv-2")

    results = memory_store.recall_episodes("Hello", conversation_id="conv-1")
    assert all(r["metadata"]["conversation_id"] == "conv-1" for r in results)


def test_search_all(memory_store):
    memory_store.store_fact("Python is great")
    memory_store.store_episode("We discussed Python", conversation_id="c1")

    results = memory_store.search_all("Python")
    assert "facts" in results
    assert "episodes" in results
    assert len(results["facts"]) >= 1
    assert len(results["episodes"]) >= 1


def test_list_facts(memory_store):
    memory_store.store_fact("Fact 1")
    memory_store.store_fact("Fact 2")
    memory_store.store_fact("Fact 3")

    facts = memory_store.list_facts(limit=2)
    assert len(facts) == 2


def test_delete_memory(memory_store):
    doc_id = memory_store.store_fact("To be deleted")
    assert memory_store.get_stats()["semantic_count"] == 1

    memory_store.delete_memory("semantic", doc_id)
    assert memory_store.get_stats()["semantic_count"] == 0


def test_stats(memory_store):
    memory_store.store_fact("A fact")
    memory_store.store_episode("An episode", conversation_id="c1")

    stats = memory_store.get_stats()
    assert stats["episodic_count"] == 1
    assert stats["semantic_count"] == 1
