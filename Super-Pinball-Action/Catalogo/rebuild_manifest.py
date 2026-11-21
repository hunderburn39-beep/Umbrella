#!/usr/bin/env python3
"""Rebuild the catalog from the uncompressed Assets directory.

Run: python Super-Pinball-Action/Catalogo/rebuild_manifest.py
Do not scan Sprites/PNG: it is a separate full-library directory.
"""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
assets=root/"Assets"
dest=Path(__file__).with_name("manifest.json")
categories=("01_Folhas_e_paletas","02_Mesas","03_Animacoes","04_Bolas","04_Flippers")
files=[]
counts={}
for category in categories:
    folder=assets/category
    if not folder.is_dir(): raise SystemExit(f"Missing {folder}")
    current=sorted(folder.rglob("*.png"))
    counts[category]=len(current)
    files.extend(x.relative_to(assets).as_posix() for x in current)
if len(files)!=1302: raise SystemExit(f"Unexpected PNG count: {len(files)} (expected 1302)")
if len(set(files))!=len(files): raise SystemExit("Duplicate paths")
manifest={"schema":1,"source":"local uncompressed Assets","counts":counts,"files":sorted(files)}
dest.write_text(json.dumps(manifest,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
print(f"Written {dest}: {len(files)} PNGs, {counts}")
