"""ROM boot diagnostics identify exact unsupported opcode without pretending to run a game."""
import unittest
from diagnostic_rom_boot import inspect_rom

def rom_for(program: bytes, pc=0x100):
    rom = bytearray(0x100 + len(program))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = pc.to_bytes(4, "big")
    rom[0x100:] = program
    return bytes(rom)

class ROMBootDiagnosticTests(unittest.TestCase):
    def test_reports_first_unsupported_opcode(self):
        result = inspect_rom(rom_for(bytes.fromhex("4e71 ffff")), 4)
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["mnemonic"], "NOP")
        self.assertEqual(result["halt"]["pc"], 0x102)
        self.assertEqual(result["halt"]["type"], "NotImplementedError")
        self.assertFalse(result["limit_reached"])

    def test_bounded_trace_does_not_overrun(self):
        result = inspect_rom(rom_for(bytes.fromhex("4e71 4e71")), 2)
        self.assertEqual(len(result["steps"]), 2)
        self.assertTrue(result["limit_reached"])
        self.assertIsNone(result["halt"])

    def test_reset_probe_failure_is_not_hidden(self):
        with self.assertRaisesRegex(ValueError, "odd initial PC"):
            inspect_rom(rom_for(bytes.fromhex("4e71"), pc=0x101))

    def test_rejects_zero_step_budget(self):
        with self.assertRaisesRegex(ValueError, "steps"):
            inspect_rom(rom_for(bytes.fromhex("4e71")), 0)

if __name__ == "__main__":
    unittest.main()
