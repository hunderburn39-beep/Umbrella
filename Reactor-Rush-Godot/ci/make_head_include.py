#!/usr/bin/env python3
"""Embed Reactor-Rush/engine/engine.js and web/rr_bridge.js into the Web export preset (html/head_include),
so the export (and the editor's "Run in Browser") is self-contained. Run after changing either file."""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
engine = open(os.path.join(root, '..', 'Reactor-Rush', 'engine', 'engine.js'), encoding='utf-8').read()
bridge = open(os.path.join(root, 'web', 'rr_bridge.js'), encoding='utf-8').read()
for js in (engine, bridge):
    assert '</script' not in js
html = '<script>\n' + engine + '\n</script>\n<script>\n' + bridge + '\n</script>'
esc = html.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
p = os.path.join(root, 'export_presets.cfg')
cfg = open(p, encoding='utf-8').read()
cfg, n = re.subn(r'^html/head_include=".*"$', lambda m: 'html/head_include="' + esc + '"', cfg, flags=re.M)
assert n == 1, n
open(p, 'w', encoding='utf-8').write(cfg)
print('head_include:', len(html), 'chars')
