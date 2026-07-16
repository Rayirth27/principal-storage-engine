import socket
import sys


def run_diagnostic_client(host: str = "127.0.0.1", port: int = 9999) -> None:
    """Day 9: Native Client Diagnostic Utility.

    Connects directly to the low-level storage engine server socket interface
    to verify raw transmission integrity and connection lifecycles.
    """
    print("=== Storage Engine Client Diagnostic Rig ===")
    print(f"Connecting to transport gateway at {host}:{port}...")

    while True:
        try:
            user_input = input("\nEnter diagnostic payload (or 'exit' to quit): ")
            if user_input.strip().lower() == "exit":
                print("Exiting diagnostic console utility.")
                sys.exit(0)

            if not user_input.strip():
                continue

            # Open a clean socket handle for this synchronous transmission cycle
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))

            # Dispatch raw payload bytes down the network wire
            client_socket.sendall(user_input.encode("utf-8"))

            # Read the server's bidirectional response channel
            response_bytes = client_socket.recv(1024)
            print(f"[RESPONSE]: {response_bytes.decode('utf-8').strip()}")

            client_socket.close()

        except ConnectionRefusedError:
            print("[ERROR] Connection refused! Is the server engine running?")
        except KeyboardInterrupt:
            print("\nForced shutdown command intercepted. Exiting safely.")
            sys.exit(0)


if __name__ == "__main__":
    run_diagnostic_client()
