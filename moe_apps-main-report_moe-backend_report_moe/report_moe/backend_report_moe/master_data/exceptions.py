"""Domain errors for master-data CRUD (mapped to HTTP status in views)."""

from __future__ import annotations


class MasterDataError(Exception):
    def __init__(self, message: str, *, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status
