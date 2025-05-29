# monitor/socket_server.py

import os
import socket
import threading
import time
import json

from monitor.notif import log

SOCKET_PATH = f"/run/user/{os.getuid()}/ps5-idle.sock"

# Shared dictionary, should be updated from monitor.py
last_input_times = {}

def start_socket_server():
    # Ensure stale socket doesn't block us
    if os.path.exists(SOCKET_PATH):
        try:
            os.remove(SOCKET_PATH)
        except Exception as e:
            log(f"⚠️ Failed to remove stale socket: {e}")
            return

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(SOCKET_PATH)
        server.listen(1)
    except Exception as e:
        log(f"❌ Failed to bind socket: {e}")
        return

    log(f"📡 Socket server listening on {SOCKET_PATH}")

    def handle_clients():
        while True:
            try:
                conn, _ = server.accept()
                with conn:
                    now = time.time()
                    response = {
                        path: {"idle_for": now - ts}
                        for path, ts in last_input_times.items()
                    }
                    conn.sendall(json.dumps(response).encode("utf-8"))
            except Exception as e:
                log(f"⚠️ Socket error: {e}")

    thread = threading.Thread(target=handle_clients, daemon=True)
    thread.start()
