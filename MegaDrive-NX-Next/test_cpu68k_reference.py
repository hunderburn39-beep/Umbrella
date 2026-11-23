import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from bus_cycle import Phase

def make_cpu(program, pc=0x100):
    rom = bytearray(max(0x108, pc + len(program)))
    rom[0:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = pc.to_bytes(4, "big")
    rom[pc:pc + len(program)] = program
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class CPU68KReferenceTests(unittest.TestCase):
    def test_reset_vectors(self):
        cpu = make_cpu(bytes.fromhex("4e71"))
        self.assertEqual((cpu.pc, cpu.ssp), (0x100, 0xff0000))

    def test_nop_fetch(self):
        cpu = make_cpu(bytes.fromhex("4e71"))
        result = cpu.step()
        self.assertEqual((result.mnemonic, cpu.pc), ("NOP", 0x102))
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_moveq_positive(self):
        cpu = make_cpu(bytes.fromhex("7207"))
        cpu.step()
        self.assertEqual(cpu.d[1], 7)

    def test_moveq_negative(self):
        cpu = make_cpu(bytes.fromhex("74ff"))
        cpu.step()
        self.assertEqual(cpu.d[2], 0xffffffff)

    def test_bra_short(self):
        cpu = make_cpu(bytes.fromhex("60024e714e71"))
        cpu.step()
        self.assertEqual(cpu.pc, 0x104)
        self.assertEqual(cpu.step().mnemonic, "NOP")

    def test_bra_word_negative(self):
        cpu = make_cpu(bytes.fromhex("6000fffc"))
        cpu.step()
        self.assertEqual(cpu.pc, 0xfe)

    def test_unsupported_opcode_does_not_advance(self):
        cpu = make_cpu(bytes.fromhex("ffff"))
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.pc, 0x100)

    def test_stop_not_faked(self):
        cpu = make_cpu(bytes.fromhex("4e720000"))
        with self.assertRaises(NotImplementedError):
            cpu.step()

    def test_bounded_run(self):
        cpu = make_cpu(bytes.fromhex("4e714e71"))
        self.assertEqual(len(cpu.run(2)), 2)
        with self.assertRaises(ValueError):
            cpu.run(0)

    def test_odd_reset_pc(self):
        rom = bytearray(16)
        rom[4:8] = (9).to_bytes(4, "big")
        cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
        with self.assertRaises(ValueError):
            cpu.reset()

if __name__ == "__main__":
    unittest.main()
