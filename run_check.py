# run_check.py
import time
from src.storage_engine.engine import StorageEngine

def run_day_5_diagnostic():
    print("=== Day 5 Snapshot Pre-Filtering Diagnostic ===")
    db = StorageEngine()

    print("[*] Seeding RAM store...")
    # Key 1: Persistent (no TTL)
    db.set_value("persistent_key", "SECURE_VAULT_PASS")
    # Key 2: Expiring in 1 second
    db.set_value("stale_key", "EXPIRED_SESSION_TOKEN", ttl_seconds=1)

    print(f"[*] Keys currently in RAM (immediately after seeding): {list(db.store.keys())}")

    print("[*] Sleeping for 1.5 seconds to allow 'stale_key' to expire...")
    time.sleep(1.5)

    print("[*] Invoking Day 5 Pre-Filtering Strategy...")
    snapshot = db.prepare_snapshot_data()

    print("\n--- Diagnostic Results ---")
    print(f"Keys remaining in live RAM index : {list(db.store.keys())}")
    print(f"Keys captured in export snapshot : {list(snapshot.keys())}")

    # Assertions
    assert "persistent_key" in snapshot, "FAIL: Persistent key missing from snapshot!"
    assert "stale_key" not in snapshot, "FAIL: Expired key leaked into snapshot!"
    print("\n[SUCCESS] Day 5 Pre-filtering works perfectly! Expired keys were discarded.")

if __name__ == "__main__":
    run_day_5_diagnostic()