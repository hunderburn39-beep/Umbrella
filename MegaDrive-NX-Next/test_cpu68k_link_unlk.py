"""68000 LINK/UNLK stack-frame tests with bus-backed RAM."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(program):
    data = bytes.fromhex(program)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.ccr = 0x1f
    return cpu

class LinkUnlkTests(unittest.TestCase):
    def test_link_negative_frame_allocation(self):
        cpu = cpu_for("4e50 fff0")
        cpu.a[0] = 0x12345678
        self.assertEqual(cpu.step().mnemonic, "LINK An,#disp16")
        self.assertEqual(cpu.a[0], 0xff00fc)
        self.assertEqual(cpu.a[7], 0xff00ec)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fc), 0x1234)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fe), 0x5678)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_link_unlk_roundtrip(self):
        cpu = cpu_for("4e52 fff8 4e5a")
        cpu.a[2] = 0xff1000
        cpu.step()
        self.assertEqual(cpu.a[2], 0xff00fc)
        self.assertEqual(cpu.a[7], 0xff00f4)
        self.assertEqual(cpu.step().mnemonic, "UNLK An")
        self.assertEqual(cpu.a[2], 0xff1000)
        self.assertEqual(cpu.a[7], 0xff0100)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_link_zero_displacement(self):
        cpu = cpu_for("4e51 0000")
        cpu.a[1] = 0x11112222
        cpu.step()
        self.assertEqual(cpu.a[1], 0xff00fc)
        self.assertEqual(cpu.a[7], 0xff00fc)

    def test_unlk_invalid_frame_does_not_modify_stack(self):
        cpu = cpu_for("4e58")
        cpu.a[0] = 0xff0101
        old_sp = cpu.a[7]
        with self.assertRaisesRegex(ValueError, "invalid UNLK"):
            cpu.step()
        self.assertEqual(cpu.a[7], old_sp)

    def test_link_positive_displacement(self):
        cpu = cpu_for("4e53 0004")
        cpu.a[3] = 0x12345678
        cpu.step()
        self.assertEqual(cpu.a[3], 0xff00fc)
        self.assertEqual(cpu.a[7], 0xff0100)

if __name__ == "__main__":
    unittest.main()
