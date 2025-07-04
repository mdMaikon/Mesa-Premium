"""
Thread-safe state manager for processing operations
"""

import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessingState:
    """Processing state data structure"""

    is_processing: bool = False
    start_time: str | None = None
    last_result: dict[str, Any] | None = None
    process_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class ThreadSafeStateManager:
    """
    Thread-safe state manager for processing operations

    This class provides thread-safe access to processing state information
    using locks to prevent race conditions in multi-threaded environments.
    """

    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._state = ProcessingState()
        logger.info("ThreadSafeStateManager initialized")

    def start_processing(self, process_id: str = None) -> bool:
        """
        Start a new processing operation

        Args:
            process_id: Optional identifier for the process

        Returns:
            bool: True if processing started, False if already in progress
        """
        with self._lock:
            if self._state.is_processing:
                logger.warning(
                    f"Processing already in progress, cannot start new process {process_id}"
                )
                return False

            self._state.is_processing = True
            self._state.start_time = datetime.now().isoformat()
            self._state.process_id = (
                process_id or f"process_{int(datetime.now().timestamp())}"
            )
            self._state.last_result = None

            logger.info(f"Processing started: {self._state.process_id}")
            return True

    def finish_processing(self, result: dict[str, Any]) -> None:
        """
        Finish the current processing operation

        Args:
            result: Processing result data
        """
        with self._lock:
            self._state.is_processing = False
            self._state.last_result = result

            logger.info(f"Processing finished: {self._state.process_id}")

    def get_status(self) -> dict[str, Any]:
        """
        Get current processing status

        Returns:
            Dict containing current state information
        """
        with self._lock:
            return self._state.to_dict()

    def is_processing(self) -> bool:
        """
        Check if processing is currently active

        Returns:
            bool: True if processing is active
        """
        with self._lock:
            return self._state.is_processing

    def get_last_result(self) -> dict[str, Any] | None:
        """
        Get the last processing result

        Returns:
            Dict with last result or None if no previous processing
        """
        with self._lock:
            return self._state.last_result

    def reset_state(self) -> None:
        """
        Reset the processing state (for testing/debugging)
        """
        with self._lock:
            self._state = ProcessingState()
            logger.info("Processing state reset")

    def force_stop_processing(self) -> None:
        """
        Force stop processing (emergency use only)
        """
        with self._lock:
            if self._state.is_processing:
                logger.warning(
                    f"Force stopping processing: {self._state.process_id}"
                )
                self._state.is_processing = False
            else:
                logger.info("No processing to force stop")


# Simple state manager for compatibility
class StateManager:
    """Simple state manager for API compatibility"""

    def __init__(self):
        self._state = {}
        self._lock = threading.RLock()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value by key"""
        with self._lock:
            return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Set state value by key"""
        with self._lock:
            self._state[key] = value


# Global singleton instance
_state_manager_instance = None
_instance_lock = threading.Lock()


def get_state_manager() -> ThreadSafeStateManager:
    """
    Get the global state manager instance (singleton pattern)

    Returns:
        ThreadSafeStateManager: Global state manager instance
    """
    global _state_manager_instance

    if _state_manager_instance is None:
        with _instance_lock:
            # Double-check locking pattern
            if _state_manager_instance is None:
                _state_manager_instance = ThreadSafeStateManager()

    return _state_manager_instance
