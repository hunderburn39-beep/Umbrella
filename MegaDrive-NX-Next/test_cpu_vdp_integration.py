"""CPU-to-bus-to-VDP reference integration, with explicit readiness.

These are untimed transactions, not a verified Genesis 3 VA2 handshake.
"""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference
from vdp_address import VDPCommand

def make_cpu(words):
    code = bytes.fromhex(words)
    rom = bytearray(0x100 + len(code))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = code
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class CPUVDPIntegrationTests(unittest.TestCase):
    def test_cpu_write_vdp_register_with_external_ready(self):
        cpu = make_cpu("33fc 8144 00c0 0004")
        cpu.vdp_ready = True
        cpu.step()
        self.assertEqual(cpu.bus.vdp.registers[1], 0x44)
        self.assertEqual(cpu.bus.completed_vdp_writes, 1)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_no_ready_does_not_modify_vdp_or_count_transfer(self):
        cpu = make_cpu("33fc 8144 00c0 0004")
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.vdp.registers[1], 0)
        self.assertEqual(cpu.bus.completed_vdp_writes, 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_cpu_write_then_read_vram_via_canonical_data_port(self):
        # Set VRAM write command, write a word, then select VRAM read.
        # MOVE.W #$4000,$C00004; MOVE.W #$0000,$C00004;
        # MOVE.W #$ABCD,$C00000; MOVE.W #$0000,$C00004;
        # MOVE.W #$0000,$C00004; MOVE.W $C00000,D0.
        cpu = make_cpu(
            "33fc 4000 00c0 0004 "
            "33fc 0000 00c0 0004 "
            "33fc abcd 00c0 0000 "
            "33fc 0000 00c0 0004 "
            "33fc 0000 00c0 0004 "
            "3039 00c0 0000"
        )
        cpu.vdp_ready = True
        cpu.run(6)
        self.assertEqual(cpu.d[0] & 0xffff, 0xabcd)
        self.assertEqual(cpu.bus.completed_vdp_writes, 5)
        self.assertEqual(cpu.bus.completed_vdp_reads, 1)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_cpu_status_read_remains_unimplemented(self):
        cpu = make_cpu("3039 00c0 0004")
        cpu.vdp_ready = True
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
