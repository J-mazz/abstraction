"""
Memory and caching system for agent state and conversation history.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import diskcache as dc
from loguru import logger
from pydantic import BaseModel


class Message(BaseModel):
    """Represents a single message in the conversation."""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}


class ConversationHistory(BaseModel):
    """Manages conversation history."""
    messages: List[Message] = []
    session_id: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class CacheManager:
    """Manages caching for agent memory and state."""

    def __init__(self, cache_dir: str = "./data/cache", max_size_mb: int = 1000, ttl_hours: int = 24):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache data
            max_size_mb: Maximum cache size in megabytes
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Convert MB to bytes
        max_size_bytes = max_size_mb * 1024 * 1024

        # Initialize diskcache
        self.cache = dc.Cache(
            str(self.cache_dir),
            size_limit=max_size_bytes,
            eviction_policy='least-recently-used'
        )

        self.ttl_seconds = ttl_hours * 3600
        logger.info(f"Cache initialized at {cache_dir} with max size {max_size_mb}MB")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (uses default if None)
        """
        expire_time = ttl if ttl is not None else self.ttl_seconds
        try:
            self.cache.set(key, value, expire=expire_time)
            logger.debug(f"Cached key: {key}")
        except Exception as e:
            logger.error(f"Failed to cache key {key}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            value = self.cache.get(key, default=default)
            if value is not None:
                logger.debug(f"Cache hit: {key}")
            else:
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve key {key}: {e}")
            return default

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.cache.delete(key)
            logger.debug(f"Deleted key: {key}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            'size': self.cache.volume(),
            'count': len(self.cache),
            'hits': self.cache.stats(enable=True)[0],
            'misses': self.cache.stats(enable=True)[1]
        }

    # Conversation history methods
    def save_conversation(self, session_id: str, history: ConversationHistory) -> None:
        """Save conversation history."""
        key = f"conversation:{session_id}"
        history.updated_at = datetime.now()
        self.set(key, history.model_dump(), ttl=self.ttl_seconds * 7)  # Keep conversations for 7x longer

    def load_conversation(self, session_id: str) -> Optional[ConversationHistory]:
        """Load conversation history."""
        key = f"conversation:{session_id}"
        data = self.get(key)
        if data:
            return ConversationHistory(**data)
        return None

    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a message to conversation history."""
        history = self.load_conversation(session_id)
        if not history:
            history = ConversationHistory(session_id=session_id)

        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        history.messages.append(message)
        self.save_conversation(session_id, history)

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages from conversation history."""
        history = self.load_conversation(session_id)
        if history:
            return history.messages[-limit:]
        return []
