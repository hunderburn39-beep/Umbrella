import unittest
from z80_bridge import Z80Bridge
from z80_control import BUSREQ_ADDR, RESET_ADDR

class Z80BridgeTests(unittest.TestCase):
    def test_end_to_end_request_grant_access(self):
        bridge = Z80Bridge()
        bridge.write_control_word(RESET_ADDR, 0x0100)
        bridge.write_control_word(BUSREQ_ADDR, 0x0100)
        self.assertEqual(bridge.status_word(), 0x0100)
        with self.assertRaises(PermissionError):
            bridge.write_byte(0xA00000, 0x31)
        bridge.observe_grant(True)
        self.assertEqual(bridge.status_word(), 0)
        bridge.write_byte(0xA00000, 0x31)
        self.assertEqual(bridge.read_byte(0xA02000), 0x31)
        bridge.write_control_word(BUSREQ_ADDR, 0)
        with self.assertRaises(PermissionError):
            bridge.read_byte(0xA00000)

    def test_reset_revokes_access(self):
        bridge = Z80Bridge()
        bridge.write_control_word(RESET_ADDR, 0x0100)
        bridge.write_control_word(BUSREQ_ADDR, 0x0100)
        bridge.observe_grant(True)
        bridge.write_control_word(RESET_ADDR, 0)
        with self.assertRaises(PermissionError):
            bridge.read_byte(0xA00000)

    def test_no_automatic_grant(self):
        bridge = Z80Bridge()
        bridge.write_control_word(RESET_ADDR, 0x0100)
        bridge.write_control_word(BUSREQ_ADDR, 0x0100)
        self.assertFalse(bridge.control.bus_granted)

if __name__ == "__main__":
    unittest.main()
