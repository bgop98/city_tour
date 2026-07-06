from __future__ import annotations

import argparse
import socket
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8080


class TripMapHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
    }

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        if sys.stderr:
            super().log_message(format, *args)


def safe_print(message: str) -> None:
    if sys.stdout:
        print(message)


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex((host, port)) != 0


def pick_port(host: str, preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 100):
        if port_is_free(host, port):
            return port
    raise RuntimeError(f"No free localhost port found from {preferred_port} to {preferred_port + 99}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the NYC trip map on localhost.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind. Defaults to {DEFAULT_PORT}.")
    parser.add_argument("--auto-port", action="store_true", help="Use the next free port if the requested port is busy.")
    parser.add_argument("--open", action="store_true", help="Open the map in the default browser after starting.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.auto_port:
        port = pick_port(args.host, args.port)
    else:
        port = args.port
        if not port_is_free(args.host, port):
            raise RuntimeError(f"Port {port} is already in use. Pass --auto-port to choose the next free port.")
    handler = partial(TripMapHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((args.host, port), handler)
    url = f"http://{args.host}:{port}/nyc-trip-map.html"

    safe_print(f"Serving {ROOT}")
    safe_print(f"Map: {url}")
    safe_print("Press Ctrl+C to stop.")

    if args.open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        safe_print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
