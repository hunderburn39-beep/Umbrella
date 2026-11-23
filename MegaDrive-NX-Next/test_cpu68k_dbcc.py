"""68000 DBcc reference loop tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def make_cpu(program):
    payload = bytes.fromhex(program)
    rom = bytearray(0x100 + len(payload))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = payload
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class DBccTests(unittest.TestCase):
    def test_dbf_loops_then_falls_through(self):
        # MOVEQ #2,D0; NOP; DBF D0,-2 (back to DBF extension address).
        c = make_cpu("7002 4e71 51c8 fffe 4e71")
        c.step()
        c.step()
        self.assertEqual(c.step().mnemonic, "DBcc")
        self.assertEqual(c.d[0] & 0xffff, 1)
        self.assertEqual(c.pc, 0x104)
        c.step()
        self.assertEqual(c.d[0] & 0xffff, 0)
        self.assertEqual(c.pc, 0x104)
        c.step()
        self.assertEqual(c.d[0] & 0xffff, 0xffff)
        self.assertEqual(c.pc, 0x108)
        self.assertEqual(c.step().mnemonic, "NOP")

    def test_dbcc_condition_true_does_not_decrement(self):
        c = make_cpu("7000 57c8 fffe 4e71")
        c.step()  # MOVEQ #0 sets Z; DBEQ condition is true.
        c.step()
        self.assertEqual(c.d[0], 0)
        self.assertEqual(c.pc, 0x106)

    def test_dbcc_preserves_upper_word_and_flags(self):
        c = make_cpu("51c8 fffe")
        c.d[0] = 0xabcd0001
        c.ccr = 0x1f
        c.step()
        self.assertEqual(c.d[0], 0xabcd0000)
        self.assertEqual(c.ccr, 0x1f)

    def test_dbcc_zero_counter_exits(self):
        c = make_cpu("51c8 fffe 4e71")
        c.d[0] = 0
        c.step()
        self.assertEqual(c.d[0], 0xffff)
        self.assertEqual(c.pc, 0x104)

    def test_odd_taken_target_rejected(self):
        c = make_cpu("51c8 ffff")
        c.d[0] = 1
        with self.assertRaises(ValueError):
            c.step()
        self.assertEqual(c.d[0], 1)

if __name__ == "__main__":
    unittest.main()
