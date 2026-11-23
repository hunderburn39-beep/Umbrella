import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def cpu_with_program(hex_program):
    program = bytes.fromhex(hex_program)
    rom = bytearray(0x100 + len(program))
    rom[0:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = program
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class CPU68KMoveTests(unittest.TestCase):
    def test_immediate_to_work_ram(self):
        cpu = cpu_with_program("33fc abcd 00ff 0010")
        self.assertEqual(cpu.step().mnemonic, "MOVE.W #imm,(abs.l)")
        self.assertEqual(cpu.bus.memory.read_word(0xff0010), 0xabcd)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_data_register_to_ram(self):
        cpu = cpu_with_program("7207 33c1 00ff 0020")
        cpu.run(2)
        self.assertEqual(cpu.bus.memory.read_word(0xff0020), 7)

    def test_immediate_to_vdp_control_explicit_ready(self):
        cpu = cpu_with_program("33fc 8144 00c0 0004")
        cpu.vdp_ready = True
        cpu.step()
        self.assertEqual(cpu.bus.vdp.registers[1], 0x44)

    def test_vdp_not_ready_does_not_write(self):
        cpu = cpu_with_program("33fc 8144 00c0 0004")
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.vdp.registers[1], 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_vdp_data_write_after_command(self):
        cpu = cpu_with_program("33fc 8f02 00c0 0004 33fc 4000 00c0 0004 33fc 0000 00c0 0004 33fc 1234 00c0 0000")
        cpu.vdp_ready = True
        cpu.run(4)
        self.assertEqual(cpu.bus.vdp.vram.read_word(0), 0x1234)

    def test_unsupported_port_rejected(self):
        cpu = cpu_with_program("33fc 1234 00c0 0008")
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_unaligned_address_rejected(self):
        cpu = cpu_with_program("33fc 1234 00ff 0001")
        with self.assertRaises(ValueError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
