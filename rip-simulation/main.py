"""
RIP Simulator - Entry Point
Run: python main.py
Opens browser automatically at http://localhost:5000
"""
import threading
import webbrowser
import time

from app import app, socketio


def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    print("=" * 50)
    print("  RIP Protocol Simulator")
    print("  Opening in your browser...")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    threading.Thread(target=open_browser, daemon=True).start()
    socketio.run(app, debug=False, port=5000, host="localhost")