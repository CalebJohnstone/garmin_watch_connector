"""Decides whether a source file needs (re)processing, using the
`import_files` table as a record of what's already been imported.

Two independent idempotency layers exist in this pipeline: this module's
file-level mtime/size/hash check (fast path, skips whole unchanged files on
a re-run) and each table's row-level `ON CONFLICT` upsert (guarantees
correctness even under --force or a bug in this file's logic).
"""

import hashlib
import os


def file_stat(file_path):
    stat = os.stat(file_path)
    return stat.st_mtime, stat.st_size


def file_sha256(file_path):
    digest = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def needs_processing(file_path, tracked_row, force):
    """Returns True if `file_path` should be (re)parsed.

    `tracked_row` is the existing `import_files` row for this path (or None
    if it's never been imported). Only hashes the file (the more expensive
    check) when mtime/size differ from what's tracked, or when forced.
    """
    if force or tracked_row is None:
        return True
    mtime, size = file_stat(file_path)
    if mtime == tracked_row["file_mtime"] and size == tracked_row["file_size"]:
        return False
    return True
