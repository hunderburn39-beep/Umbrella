import unittest
from cpu68k_reference import CPU68KReference
from bus_controller import ReferenceBusController

def cpu(hexcode):
    program = bytes.fromhex(hexcode)
    rom = bytearray(0x100 + len(program))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = program
    result = CPU68KReference(ReferenceBusController(bytes(rom)))
    result.reset()
    return result

class FlagsAndBranchesTests(unittest.TestCase):
    def test_moveq_zero_sets_z(self):
        c = cpu("7000")
        c.step()
        self.assertEqual(c.ccr & 15, 4)

    def test_moveq_negative_sets_n(self):
        c = cpu("70ff")
        c.step()
        self.assertEqual(c.ccr & 15, 8)

    def test_move_word_preserves_x(self):
        c = cpu("303c 0000")
        c.ccr = 0x1f
        c.step()
        self.assertEqual(c.ccr, 0x14)

    def test_cmpi_equal(self):
        c = cpu("7007 0c40 0007")
        c.run(2)
        self.assertTrue(c.ccr & 4)

    def test_cmpi_unsigned_borrow(self):
        c = cpu("7001 0c40 0002")
        c.run(2)
        self.assertTrue(c.ccr & 1)
        self.assertTrue(c.ccr & 8)

    def test_cmp_register(self):
        c = cpu("7005 7205 b041")
        c.run(3)
        self.assertTrue(c.ccr & 4)

    def test_beq_taken(self):
        c = cpu("7000 6702 7001 4e71")
        c.run(3)
        self.assertEqual(c.d[0], 0)
        self.assertEqual(c.pc, 0x108)

    def test_bne_not_taken(self):
        c = cpu("7000 6602 7001")
        c.run(3)
        self.assertEqual(c.d[0], 1)

    def test_bne_word_negative_loop(self):
        c = cpu("7001 6600 fffc")
        c.run(3)
        self.assertEqual(c.pc, 0x100)

    def test_bne_word_base_is_opcode_plus_two(self):
        c = cpu("7001 6600 0004 4e71 4e71 4e71")
        c.run(2)
        self.assertEqual(c.pc, 0x106)

    def test_beq_word_not_taken_consumes_extension(self):
        c = cpu("7001 6700 0004 4e71")
        c.run(2)
        self.assertEqual(c.pc, 0x106)

    def test_bsr_short_pushes_return_pc(self):
        c = cpu("6102 4e71 4e75")
        self.assertEqual(c.step().mnemonic, "BSR")
        self.assertEqual(c.pc, 0x104)
        self.assertEqual(c.bus.memory.read_word(0xfefffe), 0x102)
        self.assertEqual(c.step().mnemonic, "RTS")
        self.assertEqual(c.pc, 0x102)

    def test_signed_overflow_comparison(self):
        c = cpu("303c 7fff 0c40 ffff")
        c.run(2)
        self.assertEqual(c.ccr & 2, 2)

if __name__ == "__main__":
    unittest.main()
