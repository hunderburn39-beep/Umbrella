"""Analyse captured MegaDrive-NX VDP handshake samples without changing chip timing.

Usage: python3 analyze_vdp_handshake.py vdp-handshake-trace.txt
The input contains sampled bus levels, not a complete transaction history.
"""
import argparse
from collections import Counter

def analyze(path):
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    header = next((line.split() for line in lines if line.startswith("clock ")), None)
    if header is None:
        raise ValueError("Missing clock column header")
    records = []
    for line in lines:
        parts = line.split()
        if len(parts) != len(header) or not parts[0].isdigit():
            continue
        item = dict(zip(header, parts))
        for key in ("clock", "cpu_as", "cpu_rw", "board_dtack", "vdp_sel",
                    "vdp_ack", "reg_disp", "reg_m5"):
            item[key] = int(item[key])
        item["addr"] = int(item["addr"], 16)
        item["data"] = int(item["data"], 16)
        records.append(item)
    if not records:
        raise ValueError("No samples")
    commands = []
    previous = None
    for r in records:
        # This trace records repeated levels; a data change while selected is
        # evidence of a command candidate, not proof of a completed write.
        if r["vdp_sel"] and (previous is None or r["data"] != previous):
            commands.append(r["data"])
        previous = r["data"]
    register_writes = [(c >> 8 & 0x1f, c & 0xff) for c in commands
                       if (c & 0xc000) == 0x8000]
    reg1 = [value for reg, value in register_writes if reg == 1]
    ack_falls = sum(a["vdp_ack"] == 1 and b["vdp_ack"] == 0
                    for a, b in zip(records, records[1:]))
    dtack_falls = sum(a["board_dtack"] == 1 and b["board_dtack"] == 0
                      for a, b in zip(records, records[1:]))
    print("samples:", len(records))
    print("address counts:", {hex(k): v for k, v in Counter(r["addr"] for r in records).items()})
    print("candidate VDP register writes:", [(hex(r), hex(v)) for r, v in register_writes])
    print("register 1 values:", [hex(v) for v in reg1])
    print("display bit in register 1:", [bool(v & 0x40) for v in reg1])
    print("vdp_ack falling edges:", ack_falls)
    print("board_dtack falling edges:", dtack_falls)
    print("reg_disp ever enabled:", any(r["reg_disp"] for r in records))
    print("reg_m5 ever enabled:", any(r["reg_m5"] for r in records))
    print("CAUTION: samples do not prove completion of CPU writes or pixel output.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trace")
    args = parser.parse_args()
    analyze(args.trace)
