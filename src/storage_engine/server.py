import logging
import signal
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

from storage_engine.engine import StorageEngine

# Configure structured logging pipeline
logging.basicConfig(
    level=logging.INFO,  # To display level - INFO ( to check ERROR in future)
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(
    "StorageServer"
)  # This is a factory function.
#It asks Python’s logging system to check for a tracker with "StorageServer" name

# In a real-world project, using the Root Logger is a major headache for two main reasons:
# You can't easily tell which component printed what!
# Setting up logger = logging.getLogger("StorageServer")
# ensures our system telemetry is modular, identifiable,
# and ready to scale as we add more files to our database engine!
# If you only use the root logging.info()
# it's all-or-nothing—you have to turn the volume up or down for the entire application at once.


def handle_client_connection(
    client_socket: socket.socket, client_address: tuple, engine: StorageEngine
) -> None:
    """
    Day 10: Worker thread logic for handling a single isolated client.
    This runs in the background, allowing the main loop to accept new users instantly.
    """
    print(f"DEBUG: Thread started for {client_address}")
    logger.info("Established secure transport link with client: %s", client_address)

    try:
        # Read incoming data chunks up to 1024 bytes
        data = client_socket.recv(1024)
        if data:
            decoded_message = data.decode("utf-8").strip()
            logger.info("Received raw payload from client: '%s'", decoded_message)

            response = f"SERVER_ECHO: {decoded_message}\n"
            client_socket.sendall(response.encode("utf-8"))

    except OSError as stream_error:
        logger.error("Active socket stream broke during I/O: %s", stream_error)
    finally:
        client_socket.close()
        logger.info("Closed client socket transport handle smoothly for %s.", client_address)


def run_server(host: str = "127.0.0.1", port: int = 9999) -> None:
    """Day 10: Bounded Multi-Threaded Server Bootstrapper."""

    logger.info("Initializing Storage Engine infrastructure...")
    engine = StorageEngine()  # Reloaded old data from dump.json
    #ensuring data integrity before opening ports

    snapshot_path = "../../dump.json"
    engine.load_from_disk(snapshot_path)  # LOAD THE DATA BEFORE OPEN THE PORT

    # Capacity Ceiling Configuration
    MAX_WORKERS = 10

    # Initialize raw TCP IP socket

    signal.signal(
        signal.SIGINT, shutdown_handler
    )  # Using this we are not replying on Python's KetboardInterrupt - Triggered by Ctrl+C
    signal.signal(signal.SIGTERM, shutdown_handler)  # Triggered by OS

    server_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM
    )  # Here we tell the OS that we want to you TCP
    server_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
    )  # Using the SO_REUSEADDR - we use the port 9999 immediately whenever I want

    server_socket.bind(
        (host, port)
    )
    server_socket.listen(5)  # Backlog queue limit set to 5 pendingconnections
    logger.info("Network doors active. Listening on raw TCP bound to %s:%d", host, port)
    logger.info(
        "Thread pool initialized with strict ceiling of %d concurrent workers.", MAX_WORKERS
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:  # manager
        try:
            while True:  # server running forever until it is stopped.
                print("DEBUG: Server is waiting for a new connection...")
                # Synchronously wait for an incoming client handshake
                client_socket, client_address = (
                    server_socket.accept()
                )  # The server execution stops right here.
                print(f"DEBUG: Server accepted connection from {client_address}")
                # Instantly hand the connection off to a background worker
                pool.submit(
                    handle_client_connection, client_socket, client_address, engine
                )  # Multi-threaded:

        except KeyboardInterrupt:
            logger.info("Server shutdown requested via keyboard. Closing active ports...")
        except Exception as startup_error:
            logger.critical("Catastrophic network binder crash: %s", startup_error)
            raise startup_error
        finally:
            server_socket.close()
            logger.info("Released master TCP socket interface handle safely.")


def shutdown_handler(signum, frame):
    """Day 11: Graceful interceptor for OS kill signals."""
    logger.warning(f"Caught OS Signal {signum}. Initiating graceful shutdown...")
    # This will trigger the 'finally' block in run_server()
    sys.exit(0)


if __name__ == "__main__":
    run_server()
