#!/usr/bin/env python3
"""Serve acbuyai static site locally and open the browser."""

from __future__ import annotations

import threading
import webbrowser

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8091


def main() -> None:
    import os

    os.chdir(ROOT)
    url = f"http://127.0.0.1:{PORT}/"

    def open_browser() -> None:
        webbrowser.open(url)

    threading.Timer(0.4, open_browser).start()
    server = HTTPServer(("127.0.0.1", PORT), SimpleHTTPRequestHandler)
    print(f"Serving {ROOT} at {url} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
