"""
Mock printer server — a stand-in for a real industrial inkjet printer's
Ethernet interface, for demoing and testing before real hardware arrives.

Speaks the exact same wire protocol as TcpTextPrinterDriver
(app/drivers/printer_tcp_text.py): SELECT / SET / PRINT commands terminated
by \\r\\n, ACK'd back. When a real printer with this protocol mode shows up,
you only change the IP/port in the admin panel — nothing in the app.

Usage:
    python mock_printer_server.py [port]

Then in the admin panel, set the station's Printer:
    Protocol:     TCP Text (generic message field)
    IP Address:   127.0.0.1
    Port:          9100   (or whatever you passed)

Every "print" this receives is printed to the console with all the fields
that would have gone on the physical box - box ID, weight, product, batch,
date/time - so you can visually confirm the full pipeline end-to-end.
"""
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9100


def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)
    print(f"[mock-printer] Listening on 0.0.0.0:{PORT}")
    print("[mock-printer] Waiting for a print job...")

    while True:
        conn, addr = server.accept()
        print(f"[mock-printer] Connected: {addr}")
        buffer = ""
        pending_fields = {}
        try:
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buffer += data.decode(errors="ignore")
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        if line.startswith("SELECT|"):
                            conn.sendall(b"ACK\r\n")
                        elif line.startswith("SET|"):
                            pending_fields = {}
                            for pair in line[len("SET|"):].split("|"):
                                if "=" in pair:
                                    k, v = pair.split("=", 1)
                                    pending_fields[k] = v
                            conn.sendall(b"ACK\r\n")
                        elif line.startswith("PRINT"):
                            print("=" * 44)
                            print(" PRINTED ON BOX:")
                            for k, v in pending_fields.items():
                                print(f"   {k:<12}: {v}")
                            print("=" * 44)
                            conn.sendall(b"ACK\r\n")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            print("[mock-printer] App disconnected.")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[mock-printer] Stopped.")
