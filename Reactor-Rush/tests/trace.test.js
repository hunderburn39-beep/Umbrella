'use strict';
// Run: node --test Reactor-Rush/tests/trace.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine/engine.js');

test('trace mode does not change the round: same seed -> same win, cascades, steps (20 000 rounds)', () => {
  const a = E.createRng(4242), b = E.createRng(4242);
  for (let i = 0; i < 20000; i++) {
    const x = E.playRound(a), y = E.playRoundTrace(b);
    assert.equal(y.win, x.win, 'win round ' + i); assert.equal(y.cascades, x.cascades); assert.equal(y.steps, x.steps); assert.equal(y.qm, x.qm);
  }
  assert.equal(a.next(), b.next(), 'RNG streams must stay in sync');
});

test('deterministic replay: same seed -> identical frame list', () => {
  const run = seed => { const r = E.createRng(seed), o = []; for (let i = 0; i < 300; i++) o.push(JSON.stringify(E.playRoundTrace(r).frames)); return o.join('|'); };
  assert.equal(run(99), run(99)); assert.notEqual(run(99), run(100));
});

test('frames are well formed and win frames add up to the round total', () => {
  const rng = E.createRng(7); let wins = 0, levels = 0, expl = 0, settles = 0, g3 = 0;
  for (let i = 0; i < 60000; i++) {
    const r = E.playRoundTrace(rng), f = r.frames;
    assert.equal(f[0].type, 'start'); assert.equal(f[0].grid.length, 49);
    let sum = 0;
    for (const fr of f) {
      assert.equal(fr.grid ? fr.grid.length : 49, 49);
      if (fr.type === 'win') { wins++; sum += fr.win; assert.ok(fr.clusters.length >= 1 && fr.grid.every(c => c)); for (const c of fr.clusters) { assert.ok(c.size >= 5); assert.ok(c.type >= 0 && c.type <= 7); } }
      else if (fr.type === 'settle') { settles++; assert.ok(fr.grid.every(c => c), 'settle sem buracos'); if (fr.spawn.includes('G3')) g3++; }
      else if (fr.type === 'level') { levels++; assert.ok(fr.reactor >= 1 && fr.reactor <= 4); }
      else if (fr.type === 'explosion') { expl++; assert.ok(fr.grid.some(c => c === null)); }
    }
    if (!r.capped) assert.ok(Math.abs(sum - r.win) < 1e-9, 'soma ' + sum + ' vs ' + r.win);
  }
  assert.ok(wins > 1000 && levels > 10 && expl > 10 && g3 > 0, JSON.stringify({ wins, levels, expl, settles, g3 }));
});

test('every reactor level (1-4) appears in traces, with the matching spawn', () => {
  const rng = E.createRng(31), seen = {}; const cfg = Object.assign({}, E.DEFAULTS, { qmLevels: [8, 14, 20, 26] });
  for (let i = 0; i < 30000; i++) for (const fr of E.playRoundTrace(rng, cfg).frames) if (fr.type === 'settle' && fr.reactor) { seen[fr.reactor] = (seen[fr.reactor] || 0) + 1; assert.deepEqual(fr.spawn, [fr.reactor === 1 ? 'g1' : fr.reactor === 2 ? 'g2' : 'G3']); }
  for (const l of [1, 2, 3, 4]) assert.ok(seen[l] > 0, 'nível ' + l + ' em falta ' + JSON.stringify(seen));
});

test('Gargantoon cell counts in frames: 3x3 = 9 cells, 2x2 = 4 cells', () => {
  const rng = E.createRng(5); const cfg = Object.assign({}, E.DEFAULTS, { qmLevels: [8, 14, 20, 26] }); let checked = 0;
  for (let i = 0; i < 30000; i++) for (const fr of E.playRoundTrace(rng, cfg).frames) if (fr.type === 'settle') {
    const n = k => fr.grid.filter(c => c.k === k).length; assert.equal(n('G3') % 9, 0); assert.equal(n('G2') % 4, 0); assert.equal(n('g2') % 4, 0); checked++; }
  assert.ok(checked > 1000);
});

test('overcharge (level 4) doubles only wins containing a Gargantoon piece', () => {
  const rng = E.createRng(8); const cfg = Object.assign({}, E.DEFAULTS, { qmLevels: [8, 14, 20, 26] }); let x2 = 0;
  for (let i = 0; i < 40000; i++) for (const fr of E.playRoundTrace(rng, cfg).frames) if (fr.type === 'win') for (const c of fr.clusters) {
    const base = E.clusterPay(7 - c.type, c.size, cfg); assert.ok(Math.abs(c.pay - base * (c.gargX2 ? 2 : 1)) < 1e-9); if (c.gargX2) x2++; }
  assert.ok(x2 > 20, 'x2 raro: ' + x2);
});
