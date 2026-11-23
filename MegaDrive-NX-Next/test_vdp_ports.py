import unittest
from vdp_ports import VDPPorts

class VDPPortTests(unittest.TestCase):
    def test_register_write(self):
        v = VDPPorts()
        self.assertEqual(v.write_control(0x8144), "register-write")
        self.assertEqual(v.registers[1], 0x44)

    def test_command_pair(self):
        v = VDPPorts()
        self.assertEqual(v.write_control(0x4000), "command-pending")
        self.assertEqual(v.write_control(0x0010), "command-staged")
        self.assertEqual(v.last_command, 0x40000010)
        self.assertIsNone(v.pending_command)

    def test_register_write_does_not_stage_command(self):
        v = VDPPorts()
        v.write_control(0x8F02)
        self.assertIsNone(v.pending_command)
        self.assertEqual(v.registers[15], 2)

    def test_command_second_word_may_look_like_register(self):
        v = VDPPorts()
        v.write_control(0x4000)
        self.assertEqual(v.write_control(0x8144), "command-staged")
        self.assertEqual(v.registers[1], 0)

    def test_invalid_register(self):
        with self.assertRaises(NotImplementedError):
            VDPPorts().write_control(0x9800)

    def test_no_fake_data_port(self):
        with self.assertRaises(NotImplementedError):
            VDPPorts().write_data(0x1234)

    def test_no_fake_status(self):
        with self.assertRaises(NotImplementedError):
            VDPPorts().read_status()

    def test_reset_clears_state(self):
        v = VDPPorts()
        v.write_control(0x8144)
        v.write_control(0x4000)
        v.reset()
        self.assertEqual(v.registers[1], 0)
        self.assertIsNone(v.pending_command)

    def test_invalid_word(self):
        with self.assertRaises(ValueError):
            VDPPorts().write_control(0x10000)

if __name__ == "__main__":
    unittest.main()
