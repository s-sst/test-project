"""Deterministic hashing utilities.

Determinism is a headline platform guarantee (100% reproducibility KPI).
Two helpers underpin it:

* ``canonical_json`` — a stable, whitespace- and key-order-normalised JSON
  serialisation so that logically-equal objects hash identically.
* ``sha256_*`` — content fingerprints used for framework-config versioning,
  upload de-duplication and cache keys.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, BinaryIO

_CHUNK = 1024 * 1024  # 1 MiB streaming read


def canonical_json(obj: Any) -> str:
    """Serialise ``obj`` to a canonical JSON string (sorted keys, no spaces)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_obj(obj: Any) -> str:
    """Stable content hash of any JSON-serialisable object."""
    return sha256_hex(canonical_json(obj).encode("utf-8"))


def sha256_of_stream(stream: BinaryIO) -> str:
    """Stream-hash a file-like object without loading it fully into memory.

    Restores the stream position afterwards so the caller can re-read it.
    """
    start = stream.tell() if stream.seekable() else None
    hasher = hashlib.sha256()
    for chunk in iter(lambda: stream.read(_CHUNK), b""):
        hasher.update(chunk)
    if start is not None:
        stream.seek(start)
    return hasher.hexdigest()
