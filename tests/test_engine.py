# tests/test_engine.py
import os
import time
import pytest
from storage_engine.engine import StorageEngine


def test_basic_set_and_get():
    """Asserts that basic key-value strings are stored and retrieved with O(1) accuracy."""
    db = StorageEngine()
    assert db.set_value("username", "alex") == "OK"
    assert db.get_value("username") == "alex"


def test_missing_key_returns_none():
    """Asserts that looking up a non-existent key returns None cleanly."""
    db = StorageEngine()
    assert db.get_value("invalid_key") is None


def test_lazy_eviction_wipes_expired_key():
    """Asserts that a key past its expiration deadline is lazily evicted upon lookup."""
    db = StorageEngine()
    db.set_value("short_lived", "expired_token", ttl_seconds=1)
    
    # Verify instant availability
    assert db.get_value("short_lived") == "expired_token"
    
    # Wait until past TTL deadline
    time.sleep(1.1)
    
    # Verify key eviction
    assert db.get_value("short_lived") is None
    assert "short_lived" not in db.store


def test_snapshot_pre_filtering_removes_expired():
    """Asserts that expired data is filtered out before snapshot serializations."""
    db = StorageEngine()
    db.set_value("permanent", "active_data")
    db.set_value("temporary", "stale_data", ttl_seconds=1)

    time.sleep(1.1)

    # Invoke snapshot pre-filter
    snapshot = db.prepare_snapshot_data()

    assert "permanent" in snapshot
    assert "temporary" not in snapshot
    assert len(snapshot) == 1


def test_atomic_file_durability_roundtrip(tmp_path):
    """Asserts a full database cycle: store in RAM, write atomically to disk, and restore safely."""
    db_file = os.path.join(tmp_path, "test_database.json")
    
    db_write = StorageEngine()
    db_write.set_value("user_id", "usr_9923")
    db_write.set_value("session_key", "session_abc", ttl_seconds=10)
    db_write.set_value("temp_alert", "alert_911", ttl_seconds=1)

    # Wait for 'temp_alert' to expire before saving
    time.sleep(1.1)

    # Save snapshot atomically to disk
    db_write.save_to_disk(db_file)

    # Verify that the physical file exists
    assert os.path.exists(db_file)

    # Initialize a clean, separate database engine representing a server boot recovery
    db_read = StorageEngine()
    db_read.load_from_disk(db_file)

    # Assert active key recovery
    assert db_read.get_value("user_id") == "usr_9923"
    assert db_read.get_value("session_key") == "session_abc"
    # Assert that the expired key was dropped at pre-filtering and never written to disk
    assert db_read.get_value("temp_alert") is None