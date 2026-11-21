#!/usr/bin/env node
// Check ROM-derived positions, flipper animation and the 272 PNG dependencies.
// No ROM, emulator, third-party packages or changes to source assets required.
import {readFileSync, existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
import assert from 'node:assert/strict';

const dir=dirname(fileURLToPath(import.meta.url));
const assets=join(dir,'../Assets');
const layout=JSON.parse(readFileSync(join(dir,'flipper_layout.json'),'utf8'));
const audit=JSON.parse(readFileSync(join(dir,'oam_auditoria.json'),'utf8'));
assert.equal(layout.schema,2);
assert.equal(layout.maps.length,4);
assert.equal(layout.rows.length,8);
assert.equal(audit.records.length,56);
assert.equal(audit.romSha256,layout.romSha256);
const records=new Map(audit.records.map(r=>[r.selector+':'+r.frame,r]));
assert.equal(records.size,56);
let pieces=0;
const checked=new Set();
function png(rel,w,h,alpha){
 const p=join(assets,rel);
 assert.ok(existsSync(p),'Missing image '+rel);
 const header=readFileSync(p).subarray(0,26);
 assert.equal(header.subarray(1,4).toString(),'PNG');
 assert.equal(header.readUInt32BE(16),w,'Width '+rel);
 assert.equal(header.readUInt32BE(20),h,'Height '+rel);
 if(alpha!==undefined)assert.equal(header[25],alpha?6:2,'PNG colour mode '+rel);
 checked.add(rel);
}
for(const row of layout.rows){
 assert.equal(row.frameBases.length,7);
 assert.deepEqual(row.displayRect,{
  x:208-row.rawY,y:row.rawX,width:32,height:64
 });
 for(let frame=0;frame<7;frame++){
  const record=records.get(row.selector+':'+frame);
  assert.ok(record,'Missing OAM selector '+row.selector+' frame '+frame);
  assert.equal(record.side,row.channel);
  assert.equal(record.pieces.length,2);
  for(let half=0;half<2;half++){
   const p=record.pieces[half],num=row.frameBases[frame]+16*half;
   assert.equal(p.tile,num);
   assert.equal(p.romX,row.rawX+32*half);
   assert.equal(p.romY,row.rawY);
   assert.equal(p.sizeColor,0x12);
   assert.ok(p.attributes_base&0x04,'Disabled sprite');
   assert.ok([1,3].includes((p.attributes_base>>4)&3));
   assert.equal(p.attributes_base&0x03,0,'Unexpected flip flags');
   pieces++;
   for(let bank=0;bank<4;bank++){
    const file='tile_'+String(num).padStart(5,'0')+'_0x'+num.toString(16).toUpperCase().padStart(4,'0')+'.png';
    png('04_Flippers/bank'+bank+'/'+file,32,32,true);
   }
  }
 }
}
assert.equal(pieces,112);
for(let map=0;map<4;map++){
 const m=layout.maps[map];
 assert.equal(m.mapIndex,map);
 assert.ok(m.selectors.length>=2);
 assert.ok(m.selectors.some(x=>layout.rows[x-1].channel==='left'));
 assert.ok(m.selectors.some(x=>layout.rows[x-1].channel==='right'));
 for(let bank=0;bank<4;bank++){
  for(const layer of ['background','foreground','mixed']){
   png('02_Mesas/map_'+map+'/'+layer+'_palette'+bank+'.png',224,512,layer!=='mixed');
  }
 }
}
assert.equal(checked.size,272);
console.log('OK: 4 mesas, 4 paletas, 8 grupos, 56 estados OAM, 112 peças e 272 PNG verificados.');
