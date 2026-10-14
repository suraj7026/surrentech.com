"""WSGI entry point for cPanel/CloudLinux "Setup Python App" (LiteSpeed/Passenger).

For FTP-only deploys this host cannot run ``pip install``: the deploy pipeline uploads the
pinned requirements as one archive, ``_vendor.tar.gz``, which is unpacked here into
``_vendor/`` and put first on ``sys.path`` ahead of the cPanel virtualenv.

Startup sequence: unpack vendor archive (only when its SHA-256 changes) -> load ``.env``
with python-dotenv (environment always wins) -> ``django.setup()`` -> when
``RUN_MIGRATIONS_ON_START=1``, run ``migrate`` under an exclusive file lock -> hand the
WSGI application to the server.

Startup notes go to ``tmp/startup.log``; a hard failure is written to
``tmp/startup-error.log`` and a plain 503 page is served instead of crash-looping.

DEPLOY_STAMP is rewritten by the deploy on every release so the file's contents change
and the app server restarts the app.
"""

DEPLOY_STAMP = "local"

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

VENDOR_DIR = os.path.join(PROJECT_ROOT, "_vendor")
STARTUP_LOG_DIR = os.path.join(PROJECT_ROOT, "tmp")


def _startup_note(message):
    import datetime

    try:
        os.makedirs(STARTUP_LOG_DIR, exist_ok=True)
        path = os.path.join(STARTUP_LOG_DIR, "startup.log")
        if os.path.isfile(path) and os.path.getsize(path) > 256 * 1024:
            os.replace(path, path + ".1")
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{stamp} pid={os.getpid()} {message}\n")
    except OSError:
        pass


def _err(text):
    try:
        sys.stderr.write(text)
    except (OSError, ValueError):
        pass


def _file_sha256(path):
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unpack_vendor_archive():
    import shutil
    import tarfile

    archive = os.path.join(PROJECT_ROOT, "_vendor.tar.gz")
    stamp_file = os.path.join(VENDOR_DIR, ".archive-sha256")
    if not os.path.isfile(archive):
        return False
    try:
        import fcntl
    except ImportError:
        fcntl = None  # local checks on Windows/macOS run without the lock
    os.makedirs(STARTUP_LOG_DIR, exist_ok=True)
    with open(os.path.join(STARTUP_LOG_DIR, "vendor.lock"), "a") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            wanted = _file_sha256(archive)
            if os.path.isfile(stamp_file):
                with open(stamp_file, encoding="utf-8") as handle:
                    if handle.read().strip() == wanted:
                        return False
            _startup_note("unpacking the vendor archive")
            staging = f"{VENDOR_DIR}.new-{os.getpid()}"
            shutil.rmtree(staging, ignore_errors=True)
            with tarfile.open(archive, "r:gz") as bundle:
                try:
                    bundle.extractall(staging, filter="data")
                except TypeError:
                    bundle.extractall(staging)
            with open(os.path.join(staging, ".archive-sha256"), "w", encoding="utf-8") as handle:
                handle.write(wanted)
            retired = f"{VENDOR_DIR}.old-{os.getpid()}"
            if os.path.isdir(VENDOR_DIR):
                os.rename(VENDOR_DIR, retired)
            os.rename(staging, VENDOR_DIR)
            shutil.rmtree(retired, ignore_errors=True)
            _startup_note("vendor archive unpacked")
            return True
        except Exception as error:
            _err(f"passenger_wsgi: could not unpack the vendor archive: {error!r}\n")
            return False
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


try:
    unpack_vendor_archive()
except Exception as error:
    _err(f"passenger_wsgi: vendor archive check failed: {error!r}\n")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _run_migrations_with_lock():
    from django.core.management import call_command

    os.makedirs(STARTUP_LOG_DIR, exist_ok=True)
    try:
        import fcntl
    except ImportError:
        fcntl = None
    with open(os.path.join(STARTUP_LOG_DIR, "migrate.lock"), "a") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            import io

            output = io.StringIO()
            call_command("migrate", interactive=False, verbosity=1, stdout=output, stderr=output)
            _startup_note(f"migrations applied ({output.getvalue().count('Applying ')} new)")
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _ensure_admin():
    """DJANGO_ADMIN_EMAIL + DJANGO_ADMIN_PASSWORD set: create that superuser if no superuser exists."""
    email = os.environ.get("DJANGO_ADMIN_EMAIL", "").strip()
    password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")
    if not email or not password:
        return
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return
    User.objects.create_superuser(username=email, email=email, password=password)
    _startup_note(f"created superuser {email}")


def _unavailable_application(environ, start_response):
    body = b"The site is temporarily unavailable. Please try again shortly.\n"
    start_response(
        "503 Service Unavailable",
        [("Content-Type", "text/plain; charset=utf-8"), ("Retry-After", "120")],
    )
    return [body]


def _start():
    try:
        import dotenv
    except ImportError:
        dotenv = None
    if dotenv is not None:
        dotenv.load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=False)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "surrentech_site.settings")

    import django

    django.setup()
    _startup_note(f"django {django.get_version()} set up (vendor={'yes' if VENDOR_DIR in sys.path else 'no'}, stamp={DEPLOY_STAMP})")
    if __name__ == "__main__":
        return None
    if _truthy(os.environ.get("RUN_MIGRATIONS_ON_START")):
        _run_migrations_with_lock()
        try:
            _ensure_admin()
        except Exception as error:
            _err(f"passenger_wsgi: ensure admin failed: {error!r}\n")
    from django.core.wsgi import get_wsgi_application

    return get_wsgi_application()


try:
    application = _start()
    _startup_note("ready")
except Exception:
    import traceback

    details = traceback.format_exc()
    _startup_note("FAILED (see tmp/startup-error.log)")
    try:
        os.makedirs(STARTUP_LOG_DIR, exist_ok=True)
        with open(os.path.join(STARTUP_LOG_DIR, "startup-error.log"), "w", encoding="utf-8") as handle:
            handle.write(details)
    except OSError:
        pass
    _err(details)
    if __name__ == "__main__" or _truthy(os.environ.get("PASSENGER_WSGI_STRICT")):
        raise
    application = _unavailable_application
