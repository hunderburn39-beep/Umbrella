"""Guard against accidentally claiming that a VA4 model exists."""
import unittest
from board_profiles import PROFILES, require_executable, select_profile

class BoardProfilesTest(unittest.TestCase):
    def test_legacy_available(self):
        self.assertEqual(require_executable("legacy").implementation, "nuked-md")

    def test_va4_is_explicitly_unimplemented(self):
        self.assertFalse(select_profile("md2-va4").chip_model_verified)
        with self.assertRaisesRegex(RuntimeError, "not implemented"):
            require_executable("md2-va4")

    def test_unknown_profile_fails(self):
        with self.assertRaises(ValueError):
            select_profile("unknown")

    def test_distinct_profiles(self):
        self.assertNotEqual(PROFILES["legacy"].implementation, PROFILES["md2-va4"].implementation)

if __name__ == "__main__":
    unittest.main()
