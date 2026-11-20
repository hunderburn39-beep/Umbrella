#!/usr/bin/env python3
"""Import the two existing, verified PNG archives into a local Umbrella checkout."""
import argparse, hashlib, shutil, zipfile
from pathlib import Path, PurePosixPath

PACKS = (
    ("sprites", "b2cdb7e42814ef8a01550654dfca175d4435ecea163abed70a1a3af5cd6c6336", 61378, "Sprites", "Sprites/PNG"),
    ("assets", "2dd94a2f91cb4f2a501c732f0e41a3fea379bbb9ce4a14a981b46457e9427d05", 1302, "", "Assets"),
)

def import_pack(path, expected_hash, expected_pngs, prefix, dest):
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != expected_hash:
        raise ValueError(f"Unexpected archive SHA256: {path}: {sha}")
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError("Corrupt archive")
        entries=[]
        for info in z.infolist():
            if info.is_dir(): continue
            p=PurePosixPath(info.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in info.filename:
                raise ValueError(f"Unsafe archive path: {p}")
            if prefix:
                p=p.relative_to(prefix)
            if p.suffix.lower() not in {'.png','.json','.csv','.txt','.bin','.py'}:
                raise ValueError(f"Unexpected file type: {p}")
            target=dest.joinpath(*p.parts)
            if not target.resolve().is_relative_to(dest.resolve()):
                raise ValueError(f"Unsafe target: {target}")
            entries.append((info,target))
        if len({t for _,t in entries})!=len(entries):
            raise ValueError("Duplicate archive path")
        if sum(t.suffix.lower()=='.png' for _,t in entries)!=expected_pngs:
            raise ValueError("Unexpected PNG count")
        for info,target in entries:
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src, target.open('wb') as out:
                shutil.copyfileobj(src,out)
        print(f"{dest}: {len(entries)} files, {expected_pngs} PNGs.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('sprites',type=Path)
    ap.add_argument('assets',type=Path)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=ap.parse_args()
    for key,sha,count,prefix,destination in PACKS:
        import_pack(getattr(args,key),sha,count,prefix,args.root/destination)

if __name__=='__main__':
    main()
