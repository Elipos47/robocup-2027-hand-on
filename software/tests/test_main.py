from __future__ import annotations

import unittest

from rcj2027.__main__ import _normalize_payload


class NormalizePayloadTests(unittest.TestCase):
    def test_lowercase_kind_is_uppercased(self) -> None:
        self.assertEqual(_normalize_payload("v,1"), "V,1")
        self.assertEqual(_normalize_payload("d,1,100,100"), "D,1,100,100")

    def test_already_uppercase(self) -> None:
        self.assertEqual(_normalize_payload("X,2"), "X,2")

    def test_spaces_are_stripped(self) -> None:
        self.assertEqual(_normalize_payload("  h,1  "), "H,1")

    def test_empty(self) -> None:
        self.assertEqual(_normalize_payload("   "), "")


if __name__ == "__main__":
    unittest.main()
