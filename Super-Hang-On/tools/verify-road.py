#!/usr/bin/env python3
"""Validate the existing road data against a locally supplied arcade ROM ZIP."""
import argparse, hashlib, json, pathlib, re, zipfile
p=argparse.ArgumentParser()
p.add_argument("rom",type=pathlib.Path)
args=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
with zipfile.ZipFile(args.rom) as z:
    names=z.namelist()
    assert len(names)==25, "Unexpected ROM file count"
    b=z.read("epr-10642.47")
    assert len(b)==32768
    assert hashlib.sha1(b).hexdigest()=="26f308bf96224311ddf685799d7aa29aac42dd2f"
    decoded=bytes(((b[i]>>(7-j))&1)|(((b[i+16384]>>(7-j))&1)<<1) for i in range(16384) for j in range(8))
    rows=json.loads(re.search(r"const roadROM=(\[[\s\S]*?\]);",(root/"data/road.js").read_text())[1])
    assert len(rows)==256
    result=bytearray()
    for row in rows:
        pos=0
        for start,count,pen in row:
            assert pos==start and count>0 and 0<=pen<=3
            result.extend(bytes([pen])*count)
            pos+=count
        assert pos==512
    assert bytes(result)==decoded, "ROM pixels differ"
    assert hashlib.sha256(decoded).hexdigest()=="aa56af44284c70811c03570389564187bdc1a4af675f13c36b98347154eff4df"
    print("PASS: 131072/131072 pixels match EPR-10642.47")
