from app.ingest.hashing import sha256_bytes


def test_sha256_is_stable() -> None:
    digest = sha256_bytes(b"chunky")
    assert digest == sha256_bytes(b"chunky")
    assert len(digest) == 64


def test_different_bytes_have_different_hashes() -> None:
    assert sha256_bytes(b"a") != sha256_bytes(b"b")
