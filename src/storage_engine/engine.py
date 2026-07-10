# src/storage_engine/engine.py
import json
import os
import tempfile
import time


class StorageEngine:
    """A high-performance in-memory storage engine with metadata-based key lifetimes."""

    def __init__(
        self,
    ) -> None:  # "This function does not return any value; its return value is always None."

        # The primary in-memory Hash Table index living directly in RAM
        # Internal schema: { key: {"val": value, "exp": absolute_timestamp_or_None}}
        self.store: dict[str, dict[str, any]] = {}

    def set_value(self, key: str, value: str, ttl_seconds: int | None = None) -> str:
        """Saves a string value into memory mapped to a specific lookup key with an optional TTL."""
        expiry_timestamp = time.time() + ttl_seconds if ttl_seconds else None
        self.store[key] = {"val": value, "exp": expiry_timestamp}
        return "OK"

    def get_value(self, key: str) -> str | None:
        """Looks up a key in memory with integrated active lazy eviction."""
        # 1. If the key doesn't exist at all, return None
        if key not in self.store:
            return None

        expiry_timestamp = self.store[key]["exp"]
        # 2. Check if the key has a TTL and if that TTL has passed
        if expiry_timestamp and time.time() > expiry_timestamp:
            # Lazy Eviction: clean RAM space dynamically on demand
            print(f"\n[LAZY EVICTION] Key '{key}' has expired! Evicting from RAM...")
            del self.store[key]  # Wipe the key out of memory immediately
            return None  # Return None because the data is dead

        # 3. If it hasn't expired, return the actual string value
        return self.store[key]["val"]

    def prepare_snapshot_data(self) -> dict[str, dict[str, any]]:
        """Day 5: Pre-export extraction parser.

        Screens and driops stale/expired records in memory right before they are serialized
        to physical disk tracks to prevent storage bloat."""

        current_time = time.time()  # Freeze a single timestamp to avoid clock-drift
        filtered_snapshot = {}

        for key, data in self.store.items():
            expiry = data["exp"]
            # Save key if it has no expiration OR if its expiration is in the future
            if expiry is None or expiry > current_time:
                filtered_snapshot[key] = data

        return filtered_snapshot

    def save_to_disk(self, filepath: str) -> None:
        """Day 6 Placeholder: Atomic Serialization and Hardware Flushing.

        Writng snapshot data to a temporary 'ghost' file in the same directory, flushes Python buffers,
        forces a low-level physical disk sync via fsync, and automatically renames/replaces the target file
        to guarantee crash consistency."""

        # Step 1: Pre-filter stale keys using our Dat 5 strategy
        snapshot_data = self.prepare_snapshot_data()

        # Step 2: Establish directory context and ensure it exists
        filepath_abs = os.path.abspath(filepath)
        dir_name = os.path.dirname(filepath_abs)
        os.makedirs(dir_name, exist_ok=True)

        temp_filepath = None
        try:
            # Step 3: Write to a secure NamedTemporaryFile inside the SAME directory
            # Using delete=False allows us to manually rename/replace the file after closing.
            # Writing to the same directory ensures they reside on the same physical filesystem partition.
            with tempfile.NamedTemporaryFile(
                dir=dir_name, mode="w", delete=False, suffix=".tmp", encoding="utf-8"
            ) as f:
                temp_filepath = f.name

                # Serialize clean snapshot to the temporary file
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

                # Force Python's runtime to push its internal application buffer to the OS kernel pages
                f.flush()

                # Low-level fsync system call: extracts raw file descriptor (fileno)
                # and forces the OS to block until the disk controller physically writes to the hardware blocks
                os.fsync(f.fileno())

            # Step 4: Perform Atomic Rename/Replace
            # Because the ghost file is fully flushed and on the same partition,
            # this system call swaps the directory pointers atomically.
            os.replace(temp_filepath, filepath_abs)
            print(
                f"\n[DURABILITY] Successfully serialized, hard-flushed, and atomically swapped snapshot to '{filepath}'"
            )

        except Exception as e:
            # Fallback Cleanup: If anything fails mid-process, delete the dirty temp file to prevent leakages
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass
            print(f"[-] Database serialization failed: {e}")
            raise e

    def load_from_disk(self, filepath: str) -> None:
        """Day 2 Stub & Day 8 Placeholder: Server Bootstrap Data Restoration."""
        raise NotImplementedError("Data restoration recovery will be wired on Day 8.")
