"""
Memory and caching system for agent state and conversation history.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import diskcache as dc
from loguru import logger
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in the conversation."""

    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Manages conversation history."""

    messages: List[Message] = Field(default_factory=list)
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


def dict_to_message(msg_dict: Dict[str, Any]) -> Message:
    """
    Convert a dict message (from graph state) to a Message object.

    Args:
        msg_dict: Dictionary with 'role', 'content', 'timestamp' keys

    Returns:
        Message object
    """
    timestamp_str = msg_dict.get('timestamp')
    if isinstance(timestamp_str, str):
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp = datetime.now()
    else:
        timestamp = datetime.now()

    return Message(
        role=msg_dict['role'],
        content=msg_dict['content'],
        timestamp=timestamp,
        metadata=msg_dict.get('metadata', {})
    )


def message_to_dict(message: Message) -> Dict[str, Any]:
    """
    Convert a Message object to a dict message (for graph state).

    Args:
        message: Message object

    Returns:
        Dictionary with 'role', 'content', 'timestamp' keys
    """
    return {
        'role': message.role,
        'content': message.content,
        'timestamp': message.timestamp.isoformat(),
        'metadata': message.metadata
    }


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
        try:
            hits_misses = self.cache.stats()
            if isinstance(hits_misses, tuple) and len(hits_misses) >= 2:
                hits, misses = hits_misses[:2]
            elif isinstance(hits_misses, dict):
                hits = hits_misses.get('hits', 0)
                misses = hits_misses.get('misses', 0)
            else:
                hits = misses = 0
        except Exception as exc:
            logger.warning(f"Failed to collect cache stats: {exc}")
            hits = misses = 0

        return {
            'size_bytes': self.cache.volume(),
            'count': len(self.cache),
            'hits': hits,
            'misses': misses,
        }

    # Conversation history methods
    def save_conversation(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """
        Save conversation history from graph state dict messages.

        Args:
            session_id: Session identifier
            messages: List of dict messages from graph state
        """
        key = f"conversation:{session_id}"

        # Convert dict messages to Message objects
        message_objects = [dict_to_message(msg) for msg in messages]

        history = ConversationHistory(
            session_id=session_id,
            messages=message_objects,
            updated_at=datetime.now()
        )

        self.set(key, history.model_dump(), ttl=self.ttl_seconds * 7)  # Keep conversations for 7x longer

    def load_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Load conversation history as dict messages for graph state.

        Args:
            session_id: Session identifier

        Returns:
            List of dict messages for graph state
        """
        key = f"conversation:{session_id}"
        data = self.get(key)
        if data:
            history = ConversationHistory(**data)
            # Convert Message objects back to dict messages
            return [message_to_dict(msg) for msg in history.messages]
        return []

    def add_message(self, session_id: str, message_dict: Dict[str, Any]) -> None:
        """
        Add a dict message to conversation history.

        Args:
            session_id: Session identifier
            message_dict: Dict message from graph state
        """
        current_messages = self.load_conversation(session_id)
        current_messages.append(message_dict)
        self.save_conversation(session_id, current_messages)

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent messages from conversation history as dict messages.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of dict messages for graph state
        """
        all_messages = self.load_conversation(session_id)
        return all_messages[-limit:] if all_messages else []
