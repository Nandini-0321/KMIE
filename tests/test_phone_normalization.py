"""
tests/test_phone_normalization.py — Unit tests for libphonenumber E.164 normalization.
"""
import pytest
from services.validators import normalize_phone_e164, normalize_phone


class TestPhoneNormalizationE164:
    CANONICAL = "+919876543210"

    def test_plain_10_digits(self):
        assert normalize_phone_e164("9876543210") == self.CANONICAL

    def test_spaces(self):
        assert normalize_phone_e164("98765 43210") == self.CANONICAL

    def test_hyphen(self):
        assert normalize_phone_e164("98765-43210") == self.CANONICAL

    def test_plus91_space(self):
        assert normalize_phone_e164("+91 98765 43210") == self.CANONICAL

    def test_plus91_hyphen(self):
        assert normalize_phone_e164("+91-98765-43210") == self.CANONICAL

    def test_0091_prefix(self):
        assert normalize_phone_e164("0091 98765 43210") == self.CANONICAL

    def test_leading_zero(self):
        assert normalize_phone_e164("09876543210") == self.CANONICAL

    def test_extra_spaces(self):
        assert normalize_phone_e164("   +91 9876543210   ") == self.CANONICAL

    def test_backward_compat_normalize_phone(self):
        assert normalize_phone("+91 98765 43210") == "9876543210"


class TestPhoneNormalizationInvalid:

    def test_empty_string(self):
        assert normalize_phone_e164("") is None

    def test_none_input(self):
        assert normalize_phone_e164(None) is None

    def test_whitespace_only(self):
        assert normalize_phone_e164("   ") is None

    def test_alphabetic(self):
        assert normalize_phone_e164("abcdefghij") is None

    def test_too_short(self):
        assert normalize_phone_e164("98765") is None

    def test_too_long(self):
        assert normalize_phone_e164("98765432109876") is None

    def test_starts_with_1(self):
        assert normalize_phone_e164("1234567890") is None

    def test_starts_with_5(self):
        assert normalize_phone_e164("5876543210") is None
