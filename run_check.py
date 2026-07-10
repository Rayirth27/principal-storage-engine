# run_check.py
import os
import time
from src.storage_engine.engine import StorageEngine

def run_day_6_diagnostic():
    print("=== Day 6 Atomic Disk Serialization Diagnostic ===")
    db = StorageEngine()
    target_filepath ="dump.json"

    #Cleanup any old test dump before starting
    if os.path.exists(target_filepath):
        os.remove(target_filepath)

    print("[*] Seeding RAM store...")
    # Key 1: Persistent (no TTL)
    db.set_value("auth_token", "SESSION_OK_2026")
    # Key 2: Expiring in 1 second
    db.set_value("guest_token", "EXPIRED_GUEST", ttl_seconds=1)

    print(f"[*] Keys currently in RAM (immediately after seeding): {list(db.store.keys())}")

    print("[*] Sleeping for 1.5 seconds to allow expire guest_token...")
    time.sleep(1.5)

    print("[*] Executing crash-consistent Atomic Serialization to Disk...")
    #This invokes our newly designed Day 6 pipeline
    db.save_to_disk(target_filepath)


    print("\n--- Hardware Check ---")
    if os.path.exists(target_filepath):
        print(f"[SUCCESS] Physical snapshot file was created at '{target_filepath}'")
        with open(target_filepath, "r", encoding="utf-8") as f:
            print("File Contents:")
            print(f.read())
    else:
        print("[FAILURE] No physical file was found on disk.")

if __name__ == "__main__":
    run_day_6_diagnostic()