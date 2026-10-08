from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

READ_FILE_STATE_CACHE_SIZE = 100
DEFAULT_MAX_CACHE_SIZE_BYTES = 25 * 1024 * 1024
FILE_UNCHANGED_STUB = "File unchanged since last read. The content from the earlier Read tool_result in this conversation is still current — refer to that instead of re-reading."
FILE_UNEXPECTEDLY_MODIFIED_ERROR = "File has been unexpectedly modified. Read it again before attempting to write it."


@dataclass
class FileState:
    content: str
    timestamp_ns: int
    offset: Optional[int] = None
    limit: Optional[int] = None
    is_partial: bool = False


class FileStateCache:
    def __init__(
        self, max_entries: int = READ_FILE_STATE_CACHE_SIZE, max_size_bytes: int = DEFAULT_MAX_CACHE_SIZE_BYTES
    ) -> None:
        self.max_entries = max_entries
        self.max_size_bytes = max_size_bytes
        self._store: "OrderedDict[str, FileState]" = OrderedDict()
        self._size_bytes = 0

    @staticmethod
    def _norm(path: str) -> str:
        import posixpath

        return posixpath.normpath(path)

    def get(self, path: str) -> FileState | None:
        key = self._norm(path)
        state = self._store.get(key)
        if state is not None:
            self._store.move_to_end(key)
        return state

    def has(self, path: str) -> bool:
        return self._norm(path) in self._store

    def set(self, path: str, state: FileState) -> None:
        key = self._norm(path)
        old = self._store.get(key)
        if old is not None:
            self._size_bytes -= max(1, len(old.content.encode("utf-8")))
            self._store.move_to_end(key)
        self._store[key] = state
        self._size_bytes += max(1, len(state.content.encode("utf-8")))
        self._evict()

    def delete(self, path: str) -> bool:
        key = self._norm(path)
        state = self._store.pop(key, None)
        if state is not None:
            self._size_bytes -= max(1, len(state.content.encode("utf-8")))
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        self._size_bytes = 0

    @property
    def size(self) -> int:
        return len(self._store)

    def _evict(self) -> None:
        while len(self._store) > self.max_entries:
            _, state = self._store.popitem(last=False)
            self._size_bytes -= max(1, len(state.content.encode("utf-8")))
        while self._size_bytes > self.max_size_bytes and self._store:
            _, state = self._store.popitem(last=False)
            self._size_bytes -= max(1, len(state.content.encode("utf-8")))

    def __repr__(self) -> str:
        return f"FileStateCache(entries={len(self._store)}, bytes={self._size_bytes}/{self.max_size_bytes})"
