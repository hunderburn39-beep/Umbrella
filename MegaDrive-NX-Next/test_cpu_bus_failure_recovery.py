"""Failure isolation: an unsupported CPU bus transfer must release the cycle.

These tests cover reference transaction cleanup, not hardware retries.
"""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def cpu_for(program):
    data = bytes.fromhex(program)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class FailureRecoveryTests(unittest.TestCase):
    def test_unsupported_vdp_status_read_releases_bus(self):
        cpu = cpu_for("3039 00c0 0004")
        cpu.vdp_ready = True
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertEqual(cpu.read_word(0x100), 0x3039)

    def test_unready_vdp_write_releases_bus_and_does_not_commit(self):
        cpu = cpu_for("33fc 8144 00c0 0004")
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)
        self.assertEqual(cpu.bus.completed_vdp_writes, 0)
        self.assertEqual(cpu.bus.vdp.registers[1], 0)
        self.assertEqual(cpu.read_word(0x100), 0x33fc)

    def test_unsupported_vdp_data_write_does_not_ack(self):
        cpu = cpu_for("33fc 1234 00c0 0000")
        cpu.vdp_ready = True
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)
        self.assertEqual(cpu.bus.completed_vdp_writes, 0)
        self.assertIsNone(cpu.bus.vdp.active_command)

    def test_unaligned_indirect_read_does_not_start_bus_cycle(self):
        cpu = cpu_for("4a50")
        cpu.a[0] = 0xff0001
        with self.assertRaises(ValueError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)
        self.assertEqual(cpu.read_word(0x100), 0x4a50)

    def test_out_of_range_indirect_read_does_not_alias_rom(self):
        cpu = cpu_for("4a50")
        cpu.a[0] = 0x1000100
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)
        self.assertEqual(cpu.read_word(0x100), 0x4a50)

if __name__ == "__main__":
    unittest.main()
