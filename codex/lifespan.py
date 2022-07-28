"""Start and stop daemons."""
import multiprocessing
import os
import platform

from time import sleep

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.db.models.functions import Now
from setproctitle import setproctitle

from codex.darwin_mp import force_darwin_multiprocessing_fork
from codex.librarian.librariand import LibrarianDaemon
from codex.models import AdminFlag, LibrarianStatus, Library
from codex.notifier.notifierd import Notifier
from codex.settings.logging import get_logger
from codex.version import PACKAGE_NAME


RESET_ADMIN = bool(os.environ.get("CODEX_RESET_ADMIN"))
LOG = get_logger(__name__)


def ensure_superuser():
    """Ensure there is a valid superuser."""
    if RESET_ADMIN or not User.objects.filter(is_superuser=True).exists():
        admin_user, created = User.objects.update_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True},
        )
        admin_user.set_password("admin")
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
    query = AdminFlag.objects.filter(~Q(name__in=AdminFlag.FLAG_NAMES))
    count = query.count()
    if count:
        query.delete()
        LOG.info(f"Deleted {count} orphan AdminFlags.")


def clear_library_status():
    """Unset the update_in_progress flag for all libraries."""
    count = Library.objects.filter(update_in_progress=True).update(
        update_in_progress=False, updated_at=Now()
    )
    LOG.debug(f"Reset {count} Library's update_in_progress flag")
    LibrarianStatus.objects.filter(active=True).update(
        active=False, complete=0, total=None
    )
    LOG.debug("Cleared LibrarianStatuses.")


def codex_startup():
    """Initialize the database and start the daemons."""
    if platform.system() != "Darwin":
        setproctitle(PACKAGE_NAME)
    ensure_superuser()
    init_admin_flags()
    clear_library_status()
    cache.clear()
    force_darwin_multiprocessing_fork()

    Notifier.startup()
    LibrarianDaemon.startup()


def codex_shutdown():
    """Stop the daemons."""
    LOG.info("Codex suprocesses shutting down...")
    LibrarianDaemon.shutdown()
    Notifier.shutdown()
    while multiprocessing.active_children():
        procs = multiprocessing.active_children()
        if procs:
            LOG.debug(f"Waiting on {procs}.")
        sleep(0.5)
    LOG.info("Codex subprocesses shut down.")


async def lifespan_application(_scope, receive, send):
    """Lifespan application."""
    LOG.debug("Lifespan application started.")
    while True:
        try:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await sync_to_async(codex_startup)()
                    await send({"type": "lifespan.startup.complete"})
                    LOG.debug("Lifespan startup complete.")
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed"})
                    LOG.error("Lfespan startup failed.")
                    raise exc
            elif message["type"] == "lifespan.shutdown":
                LOG.debug("Lifespan shutdown started.")
                try:
                    # block on the join
                    codex_shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                    LOG.debug("Lifespan shutdown complete.")
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed"})
                    LOG.error("Lifespan shutdown failed.")
                    raise exc
                break
        except Exception as exc:
            LOG.exception(exc)
    LOG.debug("Lifespan application stopped.")
