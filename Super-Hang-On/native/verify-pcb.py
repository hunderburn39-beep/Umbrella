#!/usr/bin/env python3
"""Verify the owner's ROM and reconstruct the two 68000 buses in memory.
No ROM content is written or published. Standard library only.
Usage: python3 verify-pcb.py /path/to/shangon.zip
"""
import argparse
import hashlib
import json
import pathlib
import struct
import zipfile
import zlib

CHIPS = """
epr-10886.133 65536 8be3cd36
epr-10884.118 65536 cb06150d
epr-10887.132 65536 8d248bb0
epr-10885.117 65536 70795f26
epr-10792.76 65536 16299d25
epr-10790.58 65536 2246cbc1
epr-10793.75 65536 d9525427
epr-10791.57 65536 5faf4cbe
epr-10652.54 32768 260286f9
epr-10651.55 32768 c609ee7b
epr-10650.56 32768 b236a403
mpr-10794.8 131072 7c958e63
mpr-10798.16 131072 7d58f807
mpr-10795.6 131072 d9d31f8c
mpr-10799.14 131072 96d90d3d
mpr-10796.4 131072 fb48957c
mpr-10800.12 131072 feaff98e
mpr-10797.2 131072 27f2870d
mpr-10801.10 131072 12781795
epr-10642.47 32768 7836bcc3
epr-10649c.88 32768 f6c1ce71
epr-10643.66 32768 06f55364
epr-10644.67 32768 b41d541d
epr-10645.68 32768 a60dabff
epr-10646.69 32768 473cc411
""".strip().splitlines()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def audit(path):
    data = []
    with zipfile.ZipFile(path) as z:
        names = {}
        for entry in z.infolist():
            if entry.is_dir():
                continue
            name = pathlib.PurePosixPath(entry.filename).name
            require(name not in names, "Duplicate ROM: " + name)
            names[name] = entry
        for line in CHIPS:
            name, length, crc = line.split()
            require(name in names, "Missing " + name)
            require(names[name].file_size == int(length), "Wrong size: " + name)
            b = z.read(names[name])
            require(zlib.crc32(b) == int(crc, 16), "Wrong CRC: " + name)
            data.append(b)
    result = {"chips_verified": len(data), "cpus": {}}
    for name, start, stack, crc, sha in (
        ("main", 0, 0x60400, 0xfafc521a, "e4f6aab7c9ab4ed3402a0adefd2b01cb3de5c32ee22c0bdc88b7b6ecf8bef2d1"),
        ("sub", 4, 0x62000, 0xba214cdd, "770332456d5c438c8e4741b9a386e1ba8c4c2c35b59391f04609b75f9e1109a5"),
    ):
        b = bytearray(0x40000)
        for bank in range(2):
            offset = bank * 0x20000
            b[offset:offset+0x20000:2] = data[start + bank*2]
            b[offset+1:offset+0x20000:2] = data[start + bank*2+1]
        sp, pc = struct.unpack_from(">II", b)
        require((sp, pc) == (stack, 0x1000), name + " reset vectors")
        require(zlib.crc32(b) == crc, name + " bus CRC")
        require(hashlib.sha256(b).hexdigest() == sha, name + " bus SHA256")
        irq = {level: struct.unpack_from(">I", b, (24 + level)*4)[0] for level in range(1, 8)}
        expected = (
            [0x1564, 0x12ba, 0x12ba, 0x12c4, 0x12c4, 0x1564, 0x400]
            if name == "main" else
            [0x101e, 0x101e, 0x1058, 0x1058, 0x101e, 0x101e, 0x400]
        )
        require(list(irq.values()) == expected, name + " interrupt vectors")
        result["cpus"][name] = {"stack": hex(sp), "reset_pc": hex(pc), "crc32": f"{crc:08x}", "sha256": sha,
                                "interrupt_vectors": {str(k): hex(v) for k, v in irq.items()}}
    result["z80_reset"] = "0x0000"
    result["status"] = "ROM integrity and bus reconstruction PASS; execution not tested"
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom")
    print(json.dumps(audit(p.parse_args().rom), indent=2))
