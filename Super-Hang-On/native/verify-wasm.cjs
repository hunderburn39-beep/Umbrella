// Run locally after building the ROM-derived WASM. No ROM or WASM is published.
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
(async () => {
  const [dir, rom] = process.argv.slice(2);
  if (!dir || !rom) throw Error("Usage: node verify-wasm.cjs BUILD_DIR shangon.zip");
  const absolute = path.resolve(dir);
  const factory = require(path.join(absolute, "sho.js"));
  const m = await factory({wasmBinary: fs.readFileSync(path.join(absolute, "sho.wasm"))});
  const reference = fs.readFileSync(path.join(absolute, "selftest_1200.txt"), "utf8").trim().split(/\r?\n/);
  assert.equal(reference.length, 1200);
  m.FS.writeFile("/shangon.zip", fs.readFileSync(rom));
  assert.equal(m.ccall("browser_load", "number", ["string"], ["/shangon.zip"]), 0);
  assert.equal(m._browser_is_recompiled(), 1);
  m._browser_dips(0xff, 0xfe); // match the upstream coin-operated reference, not our Free Play UI
  m._browser_view_width(320);
  const hex = n => (n >>> 0).toString(16).padStart(8, "0");
  const start = Date.now();
  for (let f = 0; f < reference.length; f++) {
    const c = f % 4000;
    m._browser_input(0, +(f >= 760), 0, +((Math.floor(f/300)%4)===1),
      +(c>=700 && c<706), +(c>=600 && c<606), 0,0,0,0);
    m._browser_frame();
    assert.equal(m._browser_completed_frames()>>>0, f+1, "Frame counter");
    const hash = hex(m._browser_hash_hi()) + hex(m._browser_hash_lo());
    assert.equal(f+" "+hash, reference[f].trim(), "PCB state mismatch at frame "+f);
  }
  assert.ok(m._browser_translated_dispatches()>>>0, "No translated code executed");
  assert.ok(m._browser_sound_commands()>>>0, "No original sound commands");
  assert.equal(m._browser_width(), 320);
  assert.equal(m._browser_height(), 224);
  console.log(JSON.stringify({status:"PASS",frames:1200,seconds:(Date.now()-start)/1000,
    translatedDispatches:m._browser_translated_dispatches()>>>0,
    interpretedInstructions:m._browser_interpreted_instructions()>>>0,
    soundCommands:m._browser_sound_commands()>>>0,
    fmWrites:m._browser_fm_writes()>>>0,pcmWrites:m._browser_pcm_writes()>>>0},null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
