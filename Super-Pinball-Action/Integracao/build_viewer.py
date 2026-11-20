import base64, hashlib, json, sys, zipfile
from pathlib import Path
root=Path(sys.argv[1]); out=Path(sys.argv[2]); template=Path(__file__).with_name('viewer.html'); rom=Path(sys.argv[3])
def read(p): return json.loads(p.read_text())
def url(p,m): return 'data:'+m+';base64,'+base64.b64encode(p.read_bytes()).decode()
with zipfile.ZipFile(rom) as z:
    a,b=z.read('rom1.bin'),z.read('rom2.bin'); raw=bytearray(len(a)*2);raw[::2]=a;raw[1::2]=b
sha=hashlib.sha256(raw).hexdigest(); maps=read(root/'Fase4/results/maps.json'); trace=read(root/'Fase3/results/trace.json')
assert sha==maps['source_sha256']==trace['source_sha256']
assert len(maps['maps'])==4 and sum(m['fg_words_read'] for m in maps['maps'])==2131
assert len(trace['sprite_strips'])==87 and sum(len(s['events']) for s in trace['sequences'])==153
for i,m in enumerate(maps['maps']):
    m['images']=[{k:url(root/f'Fase4/results/map_{i}/{k}_palette{bank}.png','image/png') for k in ('mixed','background','foreground')} for bank in range(4)]
strips=[[url(root/f'Fase3/results/sprite_strips/bank{bank}/{i:03}.png','image/png') for i in range(87)] for bank in range(4)]
samples=[{'name':p.stem,'url':url(p,'audio/wav')} for p in sorted((root/'extracted/audio').glob('sample_*.wav'))]
assert len(samples)==42
D={'version':1,'source_sha256':sha,'maps':maps['maps'],'sequences':trace['sequences'],'strips':strips,'samples':samples}
s=json.dumps(D,separators=(',',':'));out.write_text(template.read_text().replace('>null</script>','>'+s+'</script>',1));print('Verified',sha,'4 maps, 4 sequences, 153 events, 348 sprite previews, 42 audio samples')
