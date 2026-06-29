# src/storage_engine/engine.py
import time

class StorageEngine:
    def __init__(self) -> None: #"This function does not return any value; its return value is always None."

        # The primary in-memory Hash Table index living directly in RAM
        self.store: dict[str, dict[str, any]]= {}

    def set_value(self, key: str, value: str, ttl_seconds: int |None = None) -> str:
        """Saves a string value into memory with an optional TTL."""
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
        Iterates over RAM cache and drops expired keys right before disk write."""

        current_time = time.time() #Freeze a single timestamp to avoid clock-drift
        filtered_snapshot={}

        for key, data in self.store.items():
            expiry = data['exp']
            #Save key if it has no expiration OR if its expiration is in the future
            if expiry is None or expiry > current_time:
                filtered_snapshot[key] = data
        
        return filtered_snapshot
    
    def save_to_disk(self, filepath: str) -> None:
        """Day 6 Placeholder: Atomic Serialization and Hardware Flushing."""
        raise NotImplementedError("Atomic disk serialization will be wired on Day 6.")



    def load_from_disk(self, filepath: str) -> None:
        """Day 2 Stub & Day 8 Placeholder: Server Bootstrap Data Restoration."""
        raise NotImplementedError("Data restoration recovery will be wired on Day 8.")
