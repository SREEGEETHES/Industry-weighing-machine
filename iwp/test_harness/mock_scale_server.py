"""
Mock scale server — a stand-in for a real RS232-to-WiFi bridge, for demoing
and testing the app before real hardware arrives.

This is NOT part of the product. It's a throwaway TCP server that speaks
exactly the same wire format a real scale bridge would: on connection, it
streams weight readings as plain text lines, the same way a real indicator
does. The app's TcpScaleDriver has no idea it's talking to a script instead
of a real bridge — which is exactly the point: when real hardware shows up,
you only change the IP/port in the admin panel, nothing in the app.

Usage:
    python mock_scale_server.py [port] [target_weight_kg]

Example:
    python mock_scale_server.py 5005 12.180

Then in the admin panel, set the station's Scale:
    Connection Type: TCP
    IP Address:      127.0.0.1
    Port:             5005   (or whatever you passed)
    Parse Pattern:    ([-+]?\d+\.?\d*)   (default, already matches this output)

Behavior: simulates someone placing a box on the scale — the reading
bounces around for ~2 seconds (like a real mechanical settle) and then
holds steady at target_weight, exactly like a real box would. Ctrl+C to
stop.
"""
import socket
import sys
import time
import random

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5005
TARGET = float(sys.argv[2]) if len(sys.argv) > 2 else 12.180


def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)
    print(f"[mock-scale] Listening on 0.0.0.0:{PORT}, will settle at {TARGET} kg")
    print("[mock-scale] Waiting for the app to connect (click 'Weigh & Print')...")

    while True:
        conn, addr = server.accept()
        print(f"[mock-scale] Connected: {addr}")
        try:
            settle_deadline = time.time() + 2.0
            with conn:
                while True:
                    if time.time() < settle_deadline:
                        # bouncing / settling, like a box being placed
                        noise = random.uniform(-0.35, 0.35)
                        value = max(0.0, TARGET + noise)
                    else:
                        # settled - real scale noise is tiny, not zero
                        value = TARGET + random.uniform(-0.003, 0.003)
                    line = f"ST,GS,+{value:07.3f},kg\r\n"
                    conn.sendall(line.encode())
                    print(f"[mock-scale] sent: {line.strip()}")
                    time.sleep(0.2)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            print("[mock-scale] App disconnected.")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[mock-scale] Stopped.")
