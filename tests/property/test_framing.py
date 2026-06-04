"""Property-based tests."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from stegox.security.framing import decrypt_payload, encrypt_payload


@given(payload=st.binary(min_size=0, max_size=2048), password=st.text(min_size=1, max_size=64))
@settings(deadline=None, max_examples=20)
def test_framing_round_trip(payload: bytes, password: str) -> None:
    frame = encrypt_payload(payload, password=password.encode("utf-8"))
    assert decrypt_payload(frame, password=password.encode("utf-8")) == payload
