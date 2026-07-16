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

        Writng snapshot data to a temporary 'ghost' file
        in the same directory, flushes Python buffers,
        forces a low-level physical disk sync via fsync, and automatically
        renames/replaces the target file
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
            # Writing to the same directory ensures
            # it resides on  same physical filesystem partition
            # Ghost File Pattern
            with tempfile.NamedTemporaryFile(
                dir=dir_name, mode="w", delete=False, suffix=".tmp", encoding="utf-8"
            ) as f:
                temp_filepath = f.name

                # Serialize clean snapshot to the temp file

                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
                f.flush()  # Force Python's runtime to push its internal
                # application buffer to the OS kernel pages

                # Low-level fsync system call: extracts raw file descriptor (fileno)
                # and forces the OS to block until
                # the disk controller physically writes to the hardware blocks
                # Hardware-Level Disk Flush
                os.fsync(f.fileno())

            # Because the ghost file is fully flushed and on the same partition,
            # this system call swaps the directory pointers atomically.
            # POSIX Automic Swap
            os.replace(
                temp_filepath, filepath_abs
            )  # Windows does this hard-flushing background work
            # automatically, we don't need extra code for Windows.

            # Principal Edge Case: Parent Directory Metadata Sync
            # POSIX systems require a folder flush;
            # Windows handles this natively via its journaling system.

            if os.name != "nt":  # If NOT Windows (Linux/macOS) - To satisfy other OS,
                # so that data corruption is impossible.
                dir_fd = os.open(dir_name, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            print(
                "\n[DURABILITY] Successfully serialized, hard-flushed, "
                f"and atomically swapped snapshot to '{filepath}' "
            )

        except Exception as e:
            if temp_filepath and os.path.exists(temp_filepath):  # Fallback Cleanup
                os.remove(temp_filepath)  # Delete the dirty temp file to prevent leakage
            raise e

    def load_from_disk(self, filepath: str) -> None:
        """Day 8: Server Bootstrap Data Restoration Recovery.
        Synchronously reads the serialized databased snapshot from disk
        validates its structure, filters out records that expired while the server
        was offline and hydrates the in-memory hash table before network doors open."""

        filepath_abs = os.path.abspath(filepath)

        # Handle fresh boot case: If no snapshot exists, initialize with clean state

        if not os.path.exists(filepath_abs):
            print(
                f"[BOOTSTRAP] No historical snapshot found at '{filepath_abs}'."
                f"Starting with a fresh, empty memory state."
            )
            self.store = {}
            return

        try:
            with open(filepath_abs, "r", encoding="utf-8") as f:
                raw_snapshot = json.load(f)

            current_time = time.time()
            hydrated_count = 0
            expired_count = 0
            temp_store = {}

            # Populate memory and run a post-offline expiry eviciton sweep
            for key, data in raw_snapshot.items():
                expiry = data.get("exp")

                # Check if the key expired while the database server was turned off
                if expiry is None or expiry > current_time:
                    temp_store[key] = data
                    hydrated_count += 1
                else:
                    expired_count += 1

            self.store = temp_store
            print(
                f"[BOOTSTRAP] Initialization complete. Hydrated {hydrated_count} active keys "
                f"into RAM. Evicted {expired_count} stale keys during recovery."
            )
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"[CRITICAL BOOT ERROR] Snapshot file at '{filepath_abs}' is corrupted: {e}")
            print("[CRITICAL] Aborting server initialization to prevent state contamination.")
            raise e
