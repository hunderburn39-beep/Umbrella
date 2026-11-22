import unittest
from va4_bus_trace import analyze, decode_row

BASE = {
    "cycle": "0", "cpu_as_n": "1", "cpu_rw": "1",
    "cpu_uds_n": "1", "cpu_lds_n": "1",
    "cpu_word_addr": "0x600002", "board_dtack_n": "1",
    "vdp_sel": "0", "vdp_as_n": "1",
    "vdp_uds_n": "1", "vdp_lds_n": "1", "vdp_ready_n": "1"
}


def sample(cycle, **kwargs):
    x = dict(BASE, cycle=str(cycle))
    x.update({k: str(v) for k, v in kwargs.items()})
    return x


class BusTraceTests(unittest.TestCase):
    def test_control_port_word_address(self):
        r = sample(0, cpu_as_n=0, cpu_rw=0, cpu_uds_n=0,
                   cpu_word_addr="0x600002")
        result = analyze([r])
        self.assertEqual(result["cpu_vdp_write"], 1)
        self.assertEqual(result["cpu_vdp_write_without_select"], 1)

    def test_complete_handshake(self):
        r = sample(0, cpu_as_n=0, cpu_rw=0, cpu_uds_n=0,
                   board_dtack_n=0, vdp_sel=1, vdp_as_n=0,
                   vdp_uds_n=0, vdp_ready_n=0)
        self.assertEqual(analyze([r])["complete_handshake"], 1)

    def test_no_false_handshake_without_strobe(self):
        r = sample(0, cpu_as_n=0, cpu_rw=0, cpu_uds_n=0,
                   board_dtack_n=0, vdp_sel=1, vdp_as_n=0,
                   vdp_ready_n=0)
        self.assertEqual(analyze([r])["complete_handshake"], 0)

    def test_wrong_address(self):
        r = sample(0, cpu_as_n=0, cpu_rw=0, cpu_uds_n=0,
                   cpu_word_addr="0x200000")
        self.assertEqual(analyze([r])["cpu_vdp_write"], 0)

    def test_cycles_monotonic(self):
        with self.assertRaises(ValueError):
            analyze([sample(2), sample(2)])

    def test_invalid_signal(self):
        with self.assertRaises(ValueError):
            decode_row(sample(0, vdp_sel=2))


if __name__ == "__main__":
    unittest.main()
