import json,struct,hashlib,sys
from pathlib import Path
def projection13(b):
 assert hashlib.sha256(b).hexdigest()=='8c139defd9b807c15872aee7e51a1fc57c8c1e4c20c764fa213d575140ca67c7'
 return {'square':list(struct.unpack_from('>256H',b,0x8e4e)), 'cross':list(struct.unpack_from('>256H',b,0x924e))}
if __name__=='__main__':
 p=projection13(Path(sys.argv[1]).read_bytes())
 assert p['square'][128]==32767==p['cross'][128]
 Path(sys.argv[2]).write_text(json.dumps(p))
