"""Short multi-instruction 68000 programs using the new ALU instruction groups."""
import unittest
from cpu68k_test_support import make_cpu, ROM_DATA, ram_word


class SumTableProgramTests(unittest.TestCase):
    def test_sum_four_rom_words_with_lea_add_dbf(self):
        program = (
            0x41fa, 0x00fe,   # 100: LEA $200(PC),A0   (extension word at $102)
            0x7203,           # 104: MOVEQ #3,D1
            0x7000,           # 106: MOVEQ #0,D0
            0xd058,           # 108: ADD.W (A0)+,D0
            0x51c9, 0xfffc,   # 10A: DBF D1,$108
        )
        table = b"".join(value.to_bytes(2, "big") for value in (1, 2, 3, 4))
        cpu = make_cpu(*program, rom_data={ROM_DATA: table})
        results = cpu.run(11)
        self.assertEqual(cpu.d[0], 10)
        self.assertEqual(cpu.d[1] & 0xffff, 0xffff)
        self.assertEqual(cpu.a[0], ROM_DATA + 8)
        self.assertEqual(cpu.pc, 0x10e)
        self.assertEqual([r.mnemonic for r in results[:4]],
                         ["LEA <ea>,An", "MOVEQ", "MOVEQ", "ADD.W <ea>,Dn"])

    def test_copy_with_mask_and_shift_into_ram(self):
        program = (
            0x203c, 0x0000, 0x1234,   # MOVE.L #$1234,D0
            0xe158,                   # ROL.W #8,D0          -> $3412
            0xc07c, 0x0ff0,           # AND.W #$0FF0,D0      -> $0410
            0x33c0, 0x00ff, 0x2000,   # MOVE.W D0,($FF2000).l
        )
        cpu = make_cpu(*program)
        cpu.run(4)
        self.assertEqual(ram_word(cpu, 0xff2000), 0x0410)


if __name__ == "__main__":
    unittest.main()
