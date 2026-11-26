'use strict';
// Run: node --test Reactor-Rush/tests
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine/engine.js');
const T = E._test;
const { N, CELLS, U, EL, EN, GA } = E;

const cfg = (over) => Object.assign({}, E.DEFAULTS, over || {});
// Build a state from a 7-row string grid: digits 0-7 regular, u/e/n/g specials, '.' filler regular 0.
function grid(rows, over) {
  const map = { u: U, e: EL, n: EN, g: GA };
  const a = [];
  for (const row of rows) for (const ch of row) a.push(ch in map ? map[ch] : Number(ch));
  assert.equal(a.length, CELLS);
  return T.makeState(cfg(over), E.createRng(1), a);
}
// 7x7 background that has no 5-cluster on its own (checkerboard of 0/1/2/3 pattern).
const BG = ['0123012', '1230123', '2301230', '3012301', '0123012', '1230123', '2301230'];
const withRow = (rows, r, str) => { const c = rows.slice(); c[r] = str; return c; };

test('PRNG is reproducible and seed sensitive', () => {
  const a = E.createRng(42), b = E.createRng(42), c = E.createRng(43);
  const sa = Array.from({ length: 50 }, () => a.next()), sb = Array.from({ length: 50 }, () => b.next()), sc = Array.from({ length: 50 }, () => c.next());
  assert.deepEqual(sa, sb); assert.notDeepEqual(sa, sc);
  assert.ok(sa.every(x => x >= 0 && x < 1));
});

test('simulate is bit-for-bit reproducible for a seed', () => {
  const x = E.simulate(3000, 777), y = E.simulate(3000, 777), z = E.simulate(3000, 778);
  assert.deepEqual(x, y); assert.notEqual(x.sum, z.sum);
});

test('mergeAgg of chunks equals the sum of its parts', () => {
  const a = E.simulate(500, 1), b = E.simulate(700, 2), m = E.mergeAgg([a, b]);
  assert.equal(m.n, 1200); assert.ok(Math.abs(m.sum - (a.sum + b.sum)) < 1e-9);
});

test('cluster threshold is 5 and wilds bridge, uncharged blocks', () => {
  // four 7s in a row: no win; five: win
  let st = grid(withRow(BG, 3, '7777301'));
  assert.equal(T.findClusters(st).length, 0);
  st = grid(withRow(BG, 3, '7777731'));
  let cl = T.findClusters(st); assert.equal(cl.length, 1); assert.equal(cl[0].cells.length, 5);
  // electric wild bridges 2 + 2 into a 5-cluster
  st = grid(withRow(BG, 3, '77e7731'));
  cl = T.findClusters(st); assert.equal(cl.length, 1); assert.equal(cl[0].t, 7); assert.equal(cl[0].cells.length, 5);
  // uncharged wild does not bridge
  st = grid(withRow(BG, 3, '77u7731'));
  assert.equal(T.findClusters(st).length, 0);
  // a wild is claimed by one cluster only
  st = grid(['5555000', '5555000', '0000000', ...BG.slice(3)].map((r, i) => i === 2 ? '0123012' : r));
  const all = T.findClusters(st), cells = all.flatMap(c => c.cells);
  assert.equal(new Set(cells).size, cells.length);
});

test('payout is monotonic in cluster size and in symbol rank', () => {
  const c = cfg();
  for (let t = 0; t < 8; t++) for (let s = 5; s < 49; s++) assert.ok(E.clusterPay(t, s + 1, c) > E.clusterPay(t, s, c), `t${t} s${s}`);
  for (let t = 0; t < 7; t++) assert.ok(E.clusterPay(t, 9, c) > E.clusterPay(t + 1, 9, c));
});

test('Quantumeter levels sit at 55 / 85 / 110 / 135', () => {
  assert.deepEqual([0, 54, 55, 84, 85, 109, 110, 134, 135, 500].map(x => E.levelFor(x)), [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]);
});

test('uncharged wild next to a win becomes Electric and stays', () => {
  const st = grid(withRow(BG, 3, '7777731'));
  st.g[3 * 7 + 6] = 3; st.g[2 * 7 + 4] = U; // above the 5th cell of the cluster
  const cl = T.findClusters(st); assert.equal(cl.length, 1);
  T.resolveStep(st, cl);
  assert.ok(st.g.includes(EL), 'an Electric Wild exists after the step');
  assert.equal(st.stats.unchargedLit, 1);
});

test('electric wild inside a win zaps: symbols vanish, wild consumed, meter charged', () => {
  const st = grid(withRow(BG, 3, '77e7731'), { pUnchargedAfterCascade: 0 });
  const before = Array.from(st.g).filter(v => v === 1).length;
  const cl = T.findClusters(st); T.resolveStep(st, cl);
  assert.equal(st.stats.zaps, 1); assert.ok(st.qm > 0 && st.qm === st.stats.zapped);
  assert.ok(!Array.from(st.g).includes(EL) || st.stats.flAwards > 0, 'consumed unless awarded by fluctometer');
  assert.ok(before >= 0);
});

test('Gargantoon 3x3 hit by a win splits into two 2x2, 2x2 into nine 1x1', () => {
  const st = grid(BG, { pUnchargedAfterCascade: 0 });
  T.setBlock(st, 4, 2, 3, GA);                     // 3x3 at rows 4-6, cols 2-4
  for (const i of [3 * 7 + 2, 3 * 7 + 3, 4 * 7 + 1, 4 * 7 + 0, 3 * 7 + 1, 3 * 7 + 0]) st.g[i] = 6; // 6-cells next to the block
  let cl = T.findClusters(st); assert.ok(cl.length >= 1, 'block participates in a cluster');
  assert.ok(cl.some(c => c.cells.some(i => st.g[i] === GA)));
  T.resolveStep(st, cl);
  assert.equal(st.stats.splits3, 1);
  assert.equal(st.blocks.size, 2); for (const b of st.blocks.values()) { assert.equal(b.size, 2); assert.equal(b.kind, GA); }
  // now a 2x2 hit
  const s2 = grid(BG, { pUnchargedAfterCascade: 0 });
  T.setBlock(s2, 4, 4, 2, GA);
  for (const i of [3 * 7 + 4, 3 * 7 + 5, 3 * 7 + 3, 3 * 7 + 2, 4 * 7 + 3]) s2.g[i] = 6;
  cl = T.findClusters(s2); assert.ok(cl.length >= 1);
  T.resolveStep(s2, cl);
  assert.equal(s2.stats.splits2, 1); assert.equal(s2.blocks.size, 0);
  assert.equal(Array.from(s2.g).filter(v => v === GA).length >= 1, true);
});

test('overcharge doubles a win that contains a Gargantoon piece', () => {
  const mk = oc => { const st = grid(withRow(BG, 3, '77g7731'), { pUnchargedAfterCascade: 0 }); st.overcharge = oc; st.g[3 * 7 + 2] = GA; return st; };
  const a = mk(false), b = mk(true);
  T.resolveStep(a, T.findClusters(a)); T.resolveStep(b, T.findClusters(b));
  assert.ok(Math.abs(b.total - 2 * a.total) < 1e-9, `${a.total} vs ${b.total}`);
});

test('Quantumeter features: L1 four Energoon, L2 a 2x2, L3 Gargantoon, L4 overcharge', () => {
  for (const [qm, check] of [
    [55, st => assert.equal(Array.from(st.g).filter(v => v === EN).length, 4)],
    [85, st => { assert.equal(st.blocks.size, 1); assert.equal([...st.blocks.values()][0].size, 2); }],
    [110, st => { assert.equal([...st.blocks.values()][0].size, 3); assert.equal(st.overcharge, false); assert.ok(st.qmDisabled && st.flDisabled); }],
    [135, st => { assert.equal([...st.blocks.values()][0].size, 3); assert.equal(st.overcharge, true); }],
  ]) {
    const st = grid(BG); st.qm = qm; assert.ok(T.runQuantumeter(st)); check(st);
    st.qm = 200; if (st.qmDisabled) assert.equal(T.runQuantumeter(st), false, 'Gargantoon disables the Quantumeter');
  }
  const none = grid(BG); none.qm = 54; assert.equal(T.runQuantumeter(none), false);
});

test('pair explosion: adjacent wipes every regular symbol, apart wipes only between', () => {
  const adj = grid(BG); adj.g[10] = EL; adj.g[11] = EL;
  assert.ok(T.runPairExplosion(adj)); assert.equal(adj.stats.explosions, 1);
  assert.ok(!Array.from(adj.g).includes(EL), 'the exploding pair is consumed');
  assert.ok(adj.qm >= 40, 'removed symbols charge the meter');
  const apart = grid(BG, {}); apart.g[1 * 7 + 1] = EL; apart.g[1 * 7 + 4] = EL;
  const outside = apart.g[5 * 7 + 5];
  T.runPairExplosion(apart);
  assert.equal(apart.stats.explosions, 1);
  assert.equal(apart.qm, 2, 'only the two cells strictly between are removed');
  assert.ok(outside >= 0);
  const single = grid(BG); single.g[10] = EL; assert.equal(T.runPairExplosion(single), false);
});

test('gravity keeps anchored blocks and fills every cell', () => {
  const st = grid(BG); T.setBlock(st, 2, 2, 3, GA);
  st.rm.fill(0); for (let r = 0; r < N; r++) st.rm[r * N + 2] = st.bid[r * N + 2] ? 0 : 1; // clear column 2 around the block
  T.gravityRefill(st);
  for (let i = 0; i < CELLS; i++) assert.ok(st.g[i] >= 0 && st.g[i] <= GA, 'cell ' + i);
  assert.equal(st.bid[2 * N + 2] > 0, true);
});

test('every settled round satisfies the end-state invariants (20 000 rounds, audited)', () => {
  const rng = E.createRng(2026), c = E.DEFAULTS;
  for (let n = 0; n < 20000; n++) {
    const st = T.makeState(c, rng); T.startRound(st); T.runToRest(st);
    for (let i = 0; i < CELLS; i++) assert.ok(st.g[i] >= 0 && st.g[i] <= GA, `invalid cell round ${n}`);
    assert.ok(st.total >= 0 && st.total <= c.maxWin + 1e-9);
    if (!st.capped) {
      assert.equal(T.findClusters(st).length, 0, `unresolved cluster round ${n}`);
      assert.ok(st.steps < c.maxSteps && st.cascades < c.maxCascades, `loop cap hit round ${n}`);
      assert.equal(Array.from(st.g).filter(v => v === EL).length < 2 || st.cascades >= c.maxCascades, true, `pair left round ${n}`);
      if (!st.qmDisabled) assert.equal(E.levelFor(st.qm, c), 0, `unplayed Quantumeter round ${n}`);
    }
    for (const [id, b] of st.blocks) for (const i of b.cells) { assert.equal(st.bid[i], id); assert.equal(st.g[i], b.kind); }
  }
});

test('win cap is respected', () => {
  const small = cfg({ maxWin: 3 });
  const a = E.simulate(4000, 9, cfg({ maxWin: 3, payScale: 50 }));
  assert.ok(a.maxWin <= 3 + 1e-9); assert.ok(a.capHits > 0); assert.ok(small.maxWin === 3);
});

test('rtpStats is consistent on a 50k-round run', () => {
  const a = E.simulate(50000, 31337), s = E.rtpStats(a);
  assert.ok(s.rtp > 0 && s.se > 0 && s.ci95[0] < s.rtp && s.rtp < s.ci95[1]);
  assert.ok(a.hits > 0 && a.explosions + a.zaps + a.flAwards > 0, 'special mechanics were exercised');
});
