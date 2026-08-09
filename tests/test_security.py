from royal_guardian.core.security import hash_password, verify_password


def test_password_hash_roundtrip():
    encoded = hash_password("a-strong-password")
    assert encoded != "a-strong-password"
    assert verify_password("a-strong-password", encoded)
    assert not verify_password("wrong-password", encoded)
