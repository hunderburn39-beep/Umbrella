#!/usr/bin/env node
// Node.js-only regression checks for the non-destructive visual blend inspector.
import {readFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script,runInNewContext} from 'node:vm';
import assert from 'node:assert/strict';

const dir=dirname(fileURLToPath(import.meta.url));
const helper=readFileSync(join(dir,'mixer_auditoria.js'),'utf8');
const html=readFileSync(join(dir,'index.html'),'utf8');
const data=JSON.parse(readFileSync(join(dir,'oam_auditoria.json'),'utf8'));
const root={};
new Script(helper,{filename:'mixer_auditoria.js'});
runInNewContext(helper,{globalThis:root,Uint8ClampedArray,Error,Object});
assert.equal(typeof root.SpaMixerAudit.auditOverlap,'function');
const audit=root.SpaMixerAudit.auditOverlap;

function px(rgb,a=255){return [...rgb,a]}
function image(...pixels){return {width:pixels.length,height:1,data:new Uint8ClampedArray(pixels.flat())}}
const fg=image(px([20,20,20]),px([20,20,20],0),px([30,30,30]),px([50,50,50]));
const combined=image(px([20,20,20]),px([20,20,20]),px([30,30,30]),px([10,10,10]));
const mixed=image(px([40,40,40]),px([90,90,90]),px([30,30,30]),px([55,55,55]));
const sprites=image(px([1,1,1]),px([1,1,1]),px([1,1,1]),px([1,1,1],0));
const stats=audit(fg,combined,mixed,sprites);
assert.equal(stats.overlapPixels,1);
assert.equal(stats.potentialBlendPixels,1);
assert.equal(stats.spritePixels,3);
assert.equal(stats.rgba[0],255);
assert.equal(stats.rgba[1],42);
assert.equal(stats.rgba[2],180);
assert.equal(stats.rgba[3],186);
for(const i of [1,2,3])assert.equal(stats.rgba[i*4+3],0);
assert.throws(()=>audit(fg,combined,mixed,{width:1,height:1,data:new Uint8ClampedArray(4)}));

// The hardware packs a colour/attribute word into a 4-bit pen address.
// MAME: color |= (attributes & 0x03f0), then gfx granularity=16;
// MAME mixer: sprite priority=(pixel >> 8) & 3.
for(const record of data.records){
 for(const piece of record.pieces){
  const color=((piece.sizeColor>>4)&15)|(piece.attributes_base&0x03f0);
  const pixel=(color<<4)|1;
  assert.equal((pixel>>8)&3,(piece.attributes_base>>4)&3);
  assert.equal((pixel>>10)&1,(piece.attributes_base>>6)&1);
  assert.ok([1,3].includes((pixel>>8)&3));
 }
}
assert.equal(data.records.length,56);

assert.ok(html.includes('<script src="mixer_auditoria.js"></script>'));
assert.ok(html.includes('id="blendAudit"'));
assert.ok(html.includes('overlayUncertain('));
const inline=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1);
assert.ok(inline,'Missing main script');
new Script(inline[1],{filename:'index-inline.js'});

console.log('OK V0.6: synthetic RGBA overlap cases, 112 sprite priorities/blend bits, inspector wiring and JS syntax.');
