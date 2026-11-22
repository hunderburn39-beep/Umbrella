"""VA4 CPU-to-VDP bus trace validator (offline diagnostic, no hardware claims).

Input CSV columns: cycle,cpu_as_n,cpu_rw,cpu_uds_n,cpu_lds_n,cpu_word_addr,
board_dtack_n,vdp_sel,vdp_as_n,vdp_uds_n,vdp_lds_n,vdp_ready_n
Logic levels: *_n = 0 means asserted; vdp_sel = 1 means selected.
Address is the 68000 *word* address, so 0xC00004 byte -> 0x600002.
Counts are sampled clock cycles, not CPU transactions.
"""
import csv
import sys

FIELDS = ("cycle", "cpu_as_n", "cpu_rw", "cpu_uds_n", "cpu_lds_n",
          "cpu_word_addr", "board_dtack_n", "vdp_sel", "vdp_as_n",
          "vdp_uds_n", "vdp_lds_n", "vdp_ready_n")


def decode_row(row):
    missing = set(FIELDS) - set(row)
    if missing:
        raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
    values = {k: int(row[k], 0) for k in FIELDS}
    for k in FIELDS:
        if k not in ("cycle", "cpu_word_addr") and values[k] not in (0, 1):
            raise ValueError(f"{k} must be 0 or 1")
    if values["cycle"] < 0 or not 0 <= values["cpu_word_addr"] < 0x800000:
        raise ValueError("Invalid cycle or 23-bit CPU word address")
    return values


def analyze(rows):
    counters = {k: 0 for k in (
        "cpu_vdp_write", "board_ack", "vdp_selected", "vdp_strobe",
        "vdp_ready", "complete_handshake", "cpu_vdp_write_without_select")}
    previous_cycle = -1
    for raw in rows:
        r = decode_row(raw)
        if r["cycle"] <= previous_cycle:
            raise ValueError("Cycle values must be strictly increasing")
        previous_cycle = r["cycle"]
        cpu_write = (r["cpu_as_n"] == 0 and r["cpu_rw"] == 0
                     and (r["cpu_uds_n"] == 0 or r["cpu_lds_n"] == 0)
                     and (r["cpu_word_addr"] & 0x700000) == 0x600000)
        selected = r["vdp_sel"] == 1 and r["vdp_as_n"] == 0
        strobe = selected and (r["vdp_uds_n"] == 0 or r["vdp_lds_n"] == 0)
        board_ack = cpu_write and r["board_dtack_n"] == 0
        ready = r["vdp_ready_n"] == 0
        counters["cpu_vdp_write"] += cpu_write
        counters["board_ack"] += board_ack
        counters["vdp_selected"] += selected
        counters["vdp_strobe"] += strobe
        counters["vdp_ready"] += ready
        counters["complete_handshake"] += cpu_write and board_ack and strobe and ready
        counters["cpu_vdp_write_without_select"] += cpu_write and not selected
    return counters


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 va4_bus_trace.py trace.csv")
    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        result = analyze(csv.DictReader(f))
    for key, value in result.items():
        print(f"{key}: {value}")
