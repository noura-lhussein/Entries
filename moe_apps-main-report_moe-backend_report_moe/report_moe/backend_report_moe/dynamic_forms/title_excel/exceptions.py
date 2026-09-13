"""Exceptions for title Excel import."""


class ImportRowError(Exception):
    def __init__(self, row: int, message: str):
        self.row = row
        self.message = message
        super().__init__(message)
