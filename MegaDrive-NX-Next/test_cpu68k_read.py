import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference
from vdp_address import VDPCommand

def make_cpu(program):
    rom = bytearray(0x100 + len(program))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = bytes.fromhex(program)
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class CPUReadTests(unittest.TestCase):
    def test_immediate_to_data_register(self):
        cpu = make_cpu("303c abcd")
        cpu.d[0] = 0x12340000
        self.assertEqual(cpu.step().mnemonic, "MOVE.W #imm,Dn")
        self.assertEqual(cpu.d[0], 0x1234abcd)

    def test_memory_to_data_register(self):
        cpu = make_cpu("3239 00ff 0010")
        cpu.bus.memory.write_word(0xff0010, 0xbeef)
        cpu.step()
        self.assertEqual(cpu.d[1], 0xbeef)

    def test_read_rom_word(self):
        cpu = make_cpu("3039 0000 0100")
        cpu.step()
        self.assertEqual(cpu.d[0], 0x3039)

    def test_cpu_ram_round_trip(self):
        cpu = make_cpu("33fc 1234 00ff 0010 3239 00ff 0010")
        cpu.run(2)
        self.assertEqual(cpu.d[1], 0x1234)

    def test_vdp_read_requires_ready(self):
        cpu = make_cpu("3039 00c0 0000")
        cpu.bus.vdp.active_command = VDPCommand(0, 0)
        cpu.bus.vdp.vram.write_word(0, 0x9876)
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_vdp_data_read_with_explicit_ready(self):
        cpu = make_cpu("3039 00c0 0000")
        cpu.bus.vdp.active_command = VDPCommand(0, 0)
        cpu.bus.vdp.vram.write_word(0, 0x9876)
        cpu.vdp_ready = True
        cpu.step()
        self.assertEqual(cpu.d[0], 0x9876)

    def test_status_port_read_not_fabricated(self):
        cpu = make_cpu("3039 00c0 0004")
        cpu.vdp_ready = True
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_unsupported_peripheral_read(self):
        cpu = make_cpu("3039 00a1 0000")
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
