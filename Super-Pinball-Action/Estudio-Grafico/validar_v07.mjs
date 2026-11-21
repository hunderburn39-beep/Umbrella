#!/usr/bin/env node
/* V0.7: test every ROM-derived flipper group, frame comparison and export model.
 * Node >=18; no browser, emulator, ROM dump or third-party dependencies.
 */
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {dirname,join} from "node:path";
import {Script,runInNewContext} from "node:vm";
const dir=dirname(fileURLToPath(import.meta.url));
const layout=JSON.parse(readFileSync(join(dir,"flipper_layout.json"),"utf8"));
const audit=JSON.parse(readFileSync(join(dir,"oam_auditoria.json"),"utf8"));
const helper=readFileSync(join(dir,"frame_auditoria.js"),"utf8");
const html=readFileSync(join(dir,"index.html"),"utf8");
const context={};
runInNewContext(helper,{globalThis:context});
const {framePair,report}=context.SpaFrameAudit;
assert.equal(audit.records.length,56);
assert.equal(layout.romSha256,audit.romSha256);
assert.deepEqual(JSON.parse(JSON.stringify(framePair("left",6,2,5))),{left:6,right:5});
assert.deepEqual(JSON.parse(JSON.stringify(framePair("right",6,2,5))),{left:2,right:6});
assert.deepEqual(JSON.parse(JSON.stringify(framePair("both",6,2,5))),{left:6,right:6});
assert.throws(()=>framePair("left",7),/Invalid/);
assert.throws(()=>framePair("missing",1),/Invalid/);
let groups=0;
for(let map=0;map<4;map++)for(let bank=0;bank<4;bank++){
 for(const mode of ["both","left","right"]){
  const result=report(layout,audit.records,map,bank,mode,2,5);
  assert.equal(result.frames.length,7);
  assert.equal(result.romSha256,layout.romSha256);
  assert.equal(result.map,map);
  assert.equal(result.bank,bank);
  for(let f=0;f<7;f++){
   const frame=result.frames[f];
   const expected=mode==="left"?{left:f,right:5}:mode==="right"?{left:2,right:f}:{left:f,right:f};
   assert.equal(frame.leftFrame,expected.left);
   assert.equal(frame.rightFrame,expected.right);
   assert.equal(frame.groups.length,layout.maps[map].selectors.length);
   for(const g of frame.groups){
    assert.ok(layout.maps[map].selectors.includes(g.selector));
    assert.equal(g.pieces.length,2);
    assert.equal(g.screenRect.width,32);
    assert.equal(g.screenRect.height,64);
    assert.equal(g.pieces[0].screenY+32,g.pieces[1].screenY);
    assert.equal(g.pieces[0].screenX,g.pieces[1].screenX);
    assert.ok([1,3].includes(g.pieces[0].priority));
    groups++;
   }
  }
 }
}
assert.equal(groups,1092);
assert.match(html,/id="sheetMode"/);
assert.match(html,/id="report"/);
assert.match(html,/src="frame_auditoria.js"/);
assert.match(html,/SpaFrameAudit\.framePair/);
assert.match(html,/SpaFrameAudit\.report/);
const main=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1);
assert.ok(main);
new Script(main[1],{filename:"index.html"});
console.log("OK V0.7: 48 combinações, 336 fotogramas, 1092 grupos OAM; JSON e JavaScript válidos.");
