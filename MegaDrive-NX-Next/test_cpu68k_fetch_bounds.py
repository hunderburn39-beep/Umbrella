"""Regression checks for explicit 24-bit reference CPU fetch bounds."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def cpu_for(program="4e71"):
    data = bytes.fromhex(program)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class FetchBoundsTests(unittest.TestCase):
    def test_regular_fetch_still_works(self):
        cpu = cpu_for()
        self.assertEqual(cpu.step().mnemonic, "NOP")
        self.assertEqual(cpu.pc, 0x102)

    def test_24_bit_overflow_does_not_alias_rom(self):
        cpu = cpu_for()
        cpu.pc = 0x1000100
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.fetch_word()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_last_even_bus_address_not_silently_wrapped(self):
        cpu = cpu_for()
        cpu.pc = 0x1000000
        with self.assertRaises(ValueError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_odd_pc_remains_invalid(self):
        cpu = cpu_for()
        cpu.pc = 0x101
        with self.assertRaisesRegex(ValueError, "odd instruction"):
            cpu.fetch_word()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
