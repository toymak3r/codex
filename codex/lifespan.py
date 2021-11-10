"""Start and stop daemons."""
import os
import platform

from logging import getLogger
from multiprocessing import set_start_method

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models.functions import Now

from codex.librarian.librariand import LibrarianDaemon
from codex.models import AdminFlag, Library
from codex.websocket_server import Notifier


RESET_ADMIN = bool(os.environ.get("CODEX_RESET_ADMIN"))
LOG = getLogger(__name__)


def ensure_superuser():
    """Ensure there is a valid superuser."""
    if RESET_ADMIN or not User.objects.filter(is_superuser=True).exists():
        admin_user, created = User.objects.update_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True},
        )
        admin_user.set_password("admin")  # type: ignore
        admin_user.save()
        prefix = "Cre" if created else "Upd"
        LOG.info(f"{prefix}ated admin user.")


def init_admin_flags():
    """Init admin flag rows."""
    for name in AdminFlag.FLAG_NAMES:
        if name in AdminFlag.DEFAULT_FALSE:
            defaults = {"on": False}
            flag, created = AdminFlag.objects.get_or_create(
                defaults=defaults, name=name
            )
        else:
            flag, created = AdminFlag.objects.get_or_create(name=name)
        if created:
            LOG.info(f"Created AdminFlag: {flag.name} = {flag.on}")


def unset_scan_in_progress():
    """Unset the scan_in_progres flag for all libraries."""
    stuck_libraries = Library.objects.filter(scan_in_progress=True).only(
        "scan_in_progress", "path"
    )
    for library in stuck_libraries:
        library.scan_in_progress = False
        library.updated_at = Now()  # type: ignore
        LOG.info(f"Removing scan lock from {library.path}")
    Library.objects.bulk_update(stuck_libraries, ["scan_in_progress"])


def codex_startup():
    """Initialize the database and start the daemons."""
    ensure_superuser()
    init_admin_flags()
    unset_scan_in_progress()
    cache.clear()

    if platform.system() == "Darwin":
        # XXX Fixes LIBRARIAN_QUEUE sharing with default spawn start method. The spawn
        # method is also very very slow. Use fork and the
        # OBJC_DISABLE_INITIALIZE_FORK_SAFETY environment variable for macOS.
        # https://bugs.python.org/issue40106
        #
        # This must happen before we create the Librarian process
        set_start_method("fork", force=True)

    Notifier.startup()
    LibrarianDaemon.startup()


def codex_shutdown():
    """Stop the daemons."""
    LibrarianDaemon.shutdown()
    Notifier.shutdown()


async def lifespan_application(_scope, receive, send):
    """Lifespan application."""
    while True:
        try:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await sync_to_async(codex_startup)()
                    await send({"type": "lifespan.startup.complete"})
                    LOG.debug("Lifespan startup complete.")
                except Exception as exc:
                    LOG.error(exc)
                    await send({"type": "lifespan.startup.failed"})
            elif message["type"] == "lifespan.shutdown":
                LOG.debug("Lifespan shutdown started.")
                try:
                    # block on the join
                    codex_shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                    LOG.debug("Lifespan shutdown complete.")
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed"})
                    LOG.error("Lfespan shutdown failed.")
                    LOG.error(exc)
                break
        except Exception as exc:
            LOG.exception(exc)
