"""Tests for shared utilities (hashing determinism)."""
from __future__ import annotations

import io

from common.hashing import canonical_json, sha256_of_obj, sha256_of_stream


def test_canonical_json_is_key_order_independent():
    a = {"b": 1, "a": 2, "nested": {"y": 1, "x": 2}}
    b = {"a": 2, "nested": {"x": 2, "y": 1}, "b": 1}
    assert canonical_json(a) == canonical_json(b)


def test_sha256_of_obj_is_deterministic():
    obj = {"framework": {"id": "x", "controls": [1, 2, 3]}}
    assert sha256_of_obj(obj) == sha256_of_obj(dict(obj))
    assert len(sha256_of_obj(obj)) == 64


def test_sha256_of_stream_restores_position():
    stream = io.BytesIO(b"hello world")
    digest = sha256_of_stream(stream)
    assert len(digest) == 64
    assert stream.tell() == 0  # position restored for re-reading
    # known sha256("hello world")
    assert digest == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
