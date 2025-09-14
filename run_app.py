# run_app.py
import os
import sys
import threading
import time
import webbrowser

def configure_paths_for_frozen():
    # When running as a PyInstaller bundle, resources are extracted to sys._MEIPASS.
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and meipass not in sys.path:
            sys.path.insert(0, meipass)

def main():
    # Ensure project modules (config, calculator) are importable
    configure_paths_for_frozen()

    # Set the correct settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    # Initialize Django
    import django
    django.setup()

    # Run migrations in-process (avoid subprocess/manage.py under PyInstaller)
    from django.core.management import call_command

    try:
        # makemigrations is optional at runtime; only needed in dev. Harmless if none.
        call_command("makemigrations", interactive=False, verbosity=0)
    except Exception:
        # Ignore if no changes or apps without migrations
        pass

    # Apply migrations
    call_command("migrate", interactive=False, verbosity=0)

    # Choose port (default 8765)
    port = os.environ.get("APP_PORT", "8765")
    addr = f"127.0.0.1:{port}"

    # Start dev server in a thread (use_reloader=False to prevent a second process)
    def run_server():
        call_command("runserver", addr, use_reloader=False, verbosity=1)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # Wait a moment for the server to bind, then open browser
    for _ in range(20):
        time.sleep(0.2)

    try:
        webbrowser.open(f"http://{addr}/license")
    except Exception:
        pass

    # Keep the main thread alive while the server runs
    try:
        while t.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()