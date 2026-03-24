"""
Launcher: khoi dong Dash server va tu mo trinh duyet.
Day la entry point thay the app.py khi dong goi .exe
"""
import sys
import threading
import webbrowser
import time

PORT = 8050
URL  = f"http://127.0.0.1:{PORT}"

def open_browser():
    """Doi server san sang roi mo trinh duyet."""
    time.sleep(2.5)
    webbrowser.open(URL)

def main():
    # Khoi dong thread mo browser
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    # Import va chay Dash app
    try:
        # Patch de an cac thong bao debug cua Dash
        import logging
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        import app as stock_app
        print(f"Server dang chay tai: {URL}")
        print("Dong cua so nay de thoat ung dung.")
        stock_app.app.run(
            debug=False,
            host="127.0.0.1",
            port=PORT,
            use_reloader=False,
        )
    except SystemExit:
        pass
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Loi khoi dong", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
