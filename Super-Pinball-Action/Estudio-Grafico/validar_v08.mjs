#!/usr/bin/env node
// Reproducible logic/syntax tests for V0.8 mobile view + motion difference.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {dirname,join} from "node:path";
import {Script,runInNewContext} from "node:vm";
const base=dirname(fileURLToPath(import.meta.url));
const js=readFileSync(join(base,"frame_diferenca.js"),"utf8");
const html=readFileSync(join(base,"index.html"),"utf8");
const layout=JSON.parse(readFileSync(join(base,"flipper_layout.json"),"utf8"));
const audit=JSON.parse(readFileSync(join(base,"oam_auditoria.json"),"utf8"));
const scope={};
runInNewContext(js,{globalThis:scope,Uint8ClampedArray});
const {compare}=scope.SpaFrameDifference;
const make=(w,h,updates=[])=>{
 const data=new Uint8ClampedArray(w*h*4);
 for(let i=0;i<w*h;i++)data[i*4+3]=255;
 for(const [x,y,c] of updates)data[(y*w+x)*4]=c;
 return {width:w,height:h,data};
};
const start=make(4,3);
const end=make(4,3,[[0,0,20],[1,2,100],[3,1,90]]);
const delta=compare(start,end);
assert.equal(delta.changedPixels,3);
assert.equal(delta.leftPixels,2);
assert.equal(delta.rightPixels,1);
assert.equal(delta.bounds.x,0);
assert.equal(delta.bounds.y,0);
assert.equal(delta.bounds.width,4);
assert.equal(delta.bounds.height,3);
assert.equal(delta.rgba[3],165);
assert.equal(delta.rgba[(1*4+2)*4+3],0);
const noChange=compare(start,make(4,3));
assert.equal(noChange.changedPixels,0);
assert.equal(noChange.bounds,null);
assert.equal(noChange.rgba.length,4*3*4);
assert.throws(()=>compare(start,make(3,3)),/Invalid/);
assert.throws(()=>compare(start,{width:4,height:3,data:new Uint8ClampedArray(4)}),/Invalid/);

// Geometric invariant for all ROM OAM pieces, independent of game physics.
let verified=0;
for(const record of audit.records){
 const row=layout.rows.find(x=>x.selector===record.selector);
 assert.ok(row);
 for(const p of record.pieces){
  assert.equal(p.romY,row.rawY);
  assert.equal((208-p.romY),row.displayRect.x);
  assert.ok(p.romX===row.rawX||p.romX===row.rawX+32);
  verified++;
 }
}
assert.equal(verified,112);
assert.ok(html.includes('id="focus"'));
assert.ok(html.includes('id="motion"'));
assert.ok(html.includes('src="frame_diferenca.js"'));
assert.ok(html.includes('body.focus-mode .stage'));
assert.ok(html.includes('overlayMotion('));
assert.ok(html.includes('code==="Escape"'));
assert.ok(html.includes('code==="KeyF"'));
const inline=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1);
assert.ok(inline);
new Script(inline[1],{filename:"index.html"});
new Script(js,{filename:"frame_diferenca.js"});
console.log("V0.8 OK: delta RGBA, exact bounds, 112 OAM pieces, controls and JavaScript syntax.");
