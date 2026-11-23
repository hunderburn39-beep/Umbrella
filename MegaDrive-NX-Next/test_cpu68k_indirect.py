"""Address-register and indirect 68000 reference regression tests."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def build_cpu(program):
    data = bytes.fromhex(program)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class CPUIndirectTests(unittest.TestCase):
    def test_reset_initializes_stack_pointer_a7(self):
        cpu = build_cpu("4e71")
        self.assertEqual(cpu.a[7], 0xff0000)

    def test_movea_immediate_long(self):
        cpu = build_cpu("207c 00ff 0040")
        self.assertEqual(cpu.step().mnemonic, "MOVEA.L #imm,An")
        self.assertEqual(cpu.a[0], 0xff0040)

    def test_movea_other_address_register(self):
        cpu = build_cpu("227c 00ff 0080")
        cpu.step()
        self.assertEqual(cpu.a[1], 0xff0080)

    def test_indirect_ram_write_and_read(self):
        # MOVEA.L #$FF0010,A0; MOVEQ #42,D0;
        # MOVE.W D0,(A0); MOVE.W (A0),D1.
        cpu = build_cpu("207c 00ff 0010 702a 3080 3210")
        result = cpu.run(4)
        self.assertEqual(result[-1].mnemonic, "MOVE.W (An),Dn")
        self.assertEqual(cpu.bus.memory.read_word(0xff0010), 42)
        self.assertEqual(cpu.d[1], 42)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_indirect_vdp_register_write_requires_ready(self):
        cpu = build_cpu("207c 00c0 0004 303c 8144 3080")
        cpu.run(2)
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.vdp.registers[1], 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_indirect_vdp_register_write_explicit_ready(self):
        cpu = build_cpu("207c 00c0 0004 303c 8144 3080")
        cpu.vdp_ready = True
        cpu.run(3)
        self.assertEqual(cpu.bus.vdp.registers[1], 0x44)

    def test_indirect_vdp_data_read_explicit_ready(self):
        cpu = build_cpu("207c 00c0 0000 3010")
        from vdp_address import VDPCommand
        cpu.bus.vdp.active_command = VDPCommand(0, 0)
        cpu.bus.vdp.vram.write_word(0, 0xabcd)
        cpu.vdp_ready = True
        cpu.run(2)
        self.assertEqual(cpu.d[0], 0xabcd)

    def test_odd_indirect_address_rejected(self):
        cpu = build_cpu("207c 00ff 0001 3010")
        cpu.step()
        with self.assertRaises(ValueError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
