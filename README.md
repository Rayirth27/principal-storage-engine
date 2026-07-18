# Principal Storage Engine

A lightweight, multi-threaded, TCP-based key-value store built in Python. Designed as a learning project to explore the principles of database internals, concurrency, and robust network programming.

---

## 🚀 Key Features

*   **Multi-Threaded Architecture:** Utilizes `ThreadPoolExecutor` to handle concurrent client connections, preventing blocking and ensuring system responsiveness.
*   **Persistent Storage:** Implements JSON-based snapshotting to ensure data integrity across server restarts.
*   **Graceful Shutdown:** Equipped with OS-level signal interceptors (`SIGINT`, `SIGTERM`) to ensure data is saved and sockets are released cleanly, preventing port-locking issues.
*   **Structured Logging:** Implements a custom telemetry layer for real-time observability.
*   **Standard Library Only:** Built from the ground up using only Python's standard library.

---

## Architecture Layers

This project follows a 5-layer separation of concerns:

1.  **Transport Layer:** Manages raw TCP connections via `socket`.
2.  **Orchestration Layer:** Manages worker threads to prevent resource exhaustion.
3.  **Application Logic:** Interprets and routes client requests.
4.  **Persistence Layer:** Manages state transitions between memory and disk (`dump.json`).
5.  **Observability Layer:** Provides system-wide logging and telemetry.

---

## 🛠️ Getting Started

### Prerequisites
*   Python 3.x

### Running the Server
Start the storage engine from the project root:

```bash
python -m src.storage_engine.server
