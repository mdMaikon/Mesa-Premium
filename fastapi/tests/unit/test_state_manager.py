"""
Unit tests for ThreadSafeStateManager
"""
import pytest
import threading
import time
from unittest.mock import patch
from utils.state_manager import ThreadSafeStateManager, get_state_manager


class TestThreadSafeStateManager:
    """Test cases for ThreadSafeStateManager"""

    def test_initial_state(self):
        """Test initial state of state manager"""
        manager = ThreadSafeStateManager()
        status = manager.get_status()
        
        assert status["is_processing"] is False
        assert status["start_time"] is None
        assert status["last_result"] is None
        assert status["process_id"] is None

    def test_start_processing_success(self):
        """Test successful start of processing"""
        manager = ThreadSafeStateManager()
        
        started = manager.start_processing("test_process")
        assert started is True
        
        status = manager.get_status()
        assert status["is_processing"] is True
        assert status["process_id"] == "test_process"
        assert status["start_time"] is not None

    def test_start_processing_already_running(self):
        """Test start processing when already running"""
        manager = ThreadSafeStateManager()
        
        # Start first process
        started1 = manager.start_processing("process1")
        assert started1 is True
        
        # Try to start second process
        started2 = manager.start_processing("process2")
        assert started2 is False
        
        # Verify first process is still running
        status = manager.get_status()
        assert status["process_id"] == "process1"

    def test_finish_processing(self):
        """Test finishing processing"""
        manager = ThreadSafeStateManager()
        
        # Start processing
        manager.start_processing("test_process")
        
        # Finish processing
        result = {"success": True, "message": "Test completed"}
        manager.finish_processing(result)
        
        status = manager.get_status()
        assert status["is_processing"] is False
        assert status["last_result"] == result

    def test_is_processing_flag(self):
        """Test is_processing flag method"""
        manager = ThreadSafeStateManager()
        
        assert manager.is_processing() is False
        
        manager.start_processing("test")
        assert manager.is_processing() is True
        
        manager.finish_processing({"success": True})
        assert manager.is_processing() is False

    def test_get_last_result(self):
        """Test get_last_result method"""
        manager = ThreadSafeStateManager()
        
        assert manager.get_last_result() is None
        
        manager.start_processing("test")
        result = {"success": True, "data": "test_data"}
        manager.finish_processing(result)
        
        assert manager.get_last_result() == result

    def test_reset_state(self):
        """Test reset_state method"""
        manager = ThreadSafeStateManager()
        
        # Set some state
        manager.start_processing("test")
        manager.finish_processing({"success": True})
        
        # Reset state
        manager.reset_state()
        
        status = manager.get_status()
        assert status["is_processing"] is False
        assert status["start_time"] is None
        assert status["last_result"] is None
        assert status["process_id"] is None

    def test_force_stop_processing(self):
        """Test force_stop_processing method"""
        manager = ThreadSafeStateManager()
        
        # Start processing
        manager.start_processing("test")
        assert manager.is_processing() is True
        
        # Force stop
        manager.force_stop_processing()
        assert manager.is_processing() is False

    def test_thread_safety(self):
        """Test thread safety with concurrent access"""
        manager = ThreadSafeStateManager()
        successful_starts = []
        
        def worker(worker_id):
            started = manager.start_processing(f"worker_{worker_id}")
            if started:
                successful_starts.append(worker_id)
                time.sleep(0.1)  # Simulate work
                manager.finish_processing({"worker_id": worker_id, "success": True})
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Only one thread should have started successfully
        assert len(successful_starts) == 1
        assert manager.is_processing() is False

    def test_process_id_generation(self):
        """Test automatic process ID generation"""
        manager = ThreadSafeStateManager()
        
        # Start without process ID
        started = manager.start_processing()
        assert started is True
        
        status = manager.get_status()
        assert status["process_id"] is not None
        assert status["process_id"].startswith("process_")


class TestStateManagerSingleton:
    """Test cases for state manager singleton pattern"""

    def test_singleton_instance(self):
        """Test that get_state_manager returns same instance"""
        manager1 = get_state_manager()
        manager2 = get_state_manager()
        
        assert manager1 is manager2

    def test_singleton_thread_safety(self):
        """Test singleton thread safety"""
        instances = []
        
        def get_instance():
            instances.append(get_state_manager())
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=get_instance)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance

    def test_singleton_state_persistence(self):
        """Test that singleton maintains state across calls"""
        manager1 = get_state_manager()
        manager1.start_processing("test_persistence")
        
        manager2 = get_state_manager()
        assert manager2.is_processing() is True
        assert manager2.get_status()["process_id"] == "test_persistence"
        
        # Clean up
        manager2.reset_state()


class TestStateManagerAsync:
    """Test cases for state manager in async context"""

    def test_async_usage(self):
        """Test state manager usage in async context"""
        import asyncio
        
        async def async_test():
            manager = ThreadSafeStateManager()
            
            # Start processing
            started = manager.start_processing("async_test")
            assert started is True
            
            # Simulate async work
            await asyncio.sleep(0.1)
            
            # Finish processing
            result = {"success": True, "async": True}
            manager.finish_processing(result)
            
            status = manager.get_status()
            assert status["is_processing"] is False
            assert status["last_result"]["async"] is True
        
        # Run async test
        asyncio.run(async_test())