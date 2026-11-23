"""CPU reset must not retain externally injected VDP readiness."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def make_cpu():
    rom = bytearray(0x108)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x108] = bytes.fromhex("33fc 8144 00c0 0004")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class ResetReadinessTests(unittest.TestCase):
    def test_reset_clears_explicit_vdp_ready(self):
        cpu = make_cpu()
        cpu.vdp_ready = True
        cpu.reset()
        self.assertFalse(cpu.vdp_ready)
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_writes, 0)
        self.assertEqual(cpu.bus.vdp.registers[1], 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_reenable_after_reset_requires_explicit_action(self):
        cpu = make_cpu()
        cpu.vdp_ready = True
        cpu.reset()
        cpu.vdp_ready = True
        self.assertEqual(cpu.step().mnemonic, "MOVE.W #imm,(abs.l)")
        self.assertEqual(cpu.bus.vdp.registers[1], 0x44)
        self.assertEqual(cpu.bus.completed_vdp_writes, 1)

    def test_reset_restores_cpu_register_state(self):
        cpu = make_cpu()
        cpu.d[0] = 0x12345678
        cpu.a[0] = 0xc00004
        cpu.ccr = 0x1f
        cpu.reset()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.a[0], 0)
        self.assertEqual(cpu.ccr, 0)
        self.assertEqual(cpu.pc, 0x100)
        self.assertEqual(cpu.a[7], 0xff0100)

if __name__ == "__main__":
    unittest.main()
