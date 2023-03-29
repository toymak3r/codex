"""Search Index cleanup."""
from time import time
from typing import Optional

from haystack.constants import DJANGO_ID
from humanize import naturaldelta
from whoosh.query import Every

from codex.librarian.search.status import SearchIndexStatusTypes
from codex.librarian.search.version import VersionMixin
from codex.models import Comic
from codex.search.backend import CodexSearchBackend
from codex.search.writing import AbortOperationError
from codex.status import Status


class RemoveMixin(VersionMixin):
    """Search Index cleanup methods."""

    @staticmethod
    def _get_delete_docnums(backend):
        """Get all the docunums that have pks that are *not* in the database."""
        database_pks = frozenset(Comic.objects.all().values_list("pk", flat=True))
        delete_docnums = []
        with backend.index.refresh().searcher() as searcher:
            results = searcher.search(Every(), scored=False)
            for result in results:
                index_pk = int(result.get(DJANGO_ID, 0))
                if index_pk not in database_pks:
                    delete_docnums.append(result.docnum)
        return delete_docnums

    def remove_stale_records(
        self, backend: Optional[CodexSearchBackend] = None  # type: ignore
    ):
        """Remove records not in the database from the index."""
        status = Status(SearchIndexStatusTypes.SEARCH_INDEX_REMOVE)
        try:
            if not self.queue.empty():
                # don't even start if something else is waiting
                raise AbortOperationError()  # noqa TRY301
            start_time = time()
            self.status_controller.start(status)
            if not backend:
                backend: CodexSearchBackend = self.engine.get_backend()  # type: ignore
            if not backend.setup_complete:
                backend.setup(False)

            delete_docnums = self._get_delete_docnums(backend)
            num_delete_docnums = len(delete_docnums)
            count = 0
            if num_delete_docnums:
                status.complete = count
                status.total = num_delete_docnums
                self.status_controller.start(status)
                count = backend.remove_docnums(
                    delete_docnums,
                    sc=self.status_controller,
                    status=status,
                    queue=self.queue,
                )

            # Finish
            if count:
                elapsed_time = time() - start_time
                elapsed = naturaldelta(elapsed_time)
                cps = int(count / elapsed_time)
                self.log.info(
                    f"Removed {count} stale records from the search index"
                    f" in {elapsed} at {cps} per second."
                )
            else:
                self.log.debug("No stale records to remove from the search index.")
        except AbortOperationError:
            # update kicks off a remove stale operations when it's done.
            # rebuild doesn't need one.
            self.log.debug("Search Index Remove Stale Records aborted.")
        except Exception:
            self.log.exception("Removing stale records:")
        finally:
            self.status_controller.finish(status)
