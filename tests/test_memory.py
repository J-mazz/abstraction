from datetime import datetime

import pytest

from src.memory.cache_manager import CacheManager, ConversationHistory, Message


@pytest.fixture
def cache_manager(tmp_path):
    return CacheManager(cache_dir=str(tmp_path / "cache"), max_size_mb=1, ttl_hours=1)


def test_cache_set_get_delete(cache_manager):
    cache_manager.set("alpha", {"value": 1})
    assert cache_manager.get("alpha")["value"] == 1

    assert cache_manager.get("missing", default="noop") == "noop"

    assert cache_manager.delete("alpha") is True
    assert cache_manager.get("alpha") is None


def test_cache_stats(cache_manager):
    cache_manager.set("beta", "data")
    stats = cache_manager.get_stats()
    assert stats["count"] >= 1
    assert stats["size_bytes"] >= 0
    assert stats["hits"] >= 0
    assert stats["misses"] >= 0


def test_conversation_roundtrip(cache_manager):
    session_id = "session-123"
    history = ConversationHistory(session_id=session_id)
    history.messages.append(
        Message(role="user", content="hi", timestamp=datetime.now(), metadata={"id": 1})
    )
    cache_manager.save_conversation(session_id, history)

    loaded = cache_manager.load_conversation(session_id)
    assert loaded is not None
    assert loaded.messages[0].role == "user"

    cache_manager.add_message(session_id, "assistant", "hey")
    recent = cache_manager.get_recent_messages(session_id, limit=2)
    assert len(recent) == 2
    assert recent[-1].role == "assistant"


def test_cache_manager_handles_backend_errors(cache_manager, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cache_manager.cache, "set", boom)
    cache_manager.set("err", "value")

    monkeypatch.setattr(cache_manager.cache, "get", boom)
    assert cache_manager.get("err", default="fallback") == "fallback"

    monkeypatch.setattr(cache_manager.cache, "delete", boom)
    assert cache_manager.delete("err") is False

    monkeypatch.setattr(cache_manager.cache, "clear", boom)
    cache_manager.clear()


def test_cache_stats_covers_dict_and_errors(cache_manager, monkeypatch):
    monkeypatch.setattr(cache_manager.cache, "stats", lambda: {"hits": 5, "misses": 1})
    stats = cache_manager.get_stats()
    assert stats["hits"] == 5 and stats["misses"] == 1

    def stats_boom():
        raise RuntimeError("fail")

    monkeypatch.setattr(cache_manager.cache, "stats", stats_boom)
    fallback = cache_manager.get_stats()
    assert fallback["hits"] == 0 and fallback["misses"] == 0


def test_get_recent_messages_without_history(cache_manager):
    assert cache_manager.get_recent_messages("missing") == []
