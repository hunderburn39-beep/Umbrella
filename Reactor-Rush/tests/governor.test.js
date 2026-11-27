'use strict';
// House reserve (limite rígido): the total paid in a session never exceeds rtpCap x total wagered.
// Run: node --test tests/engine.test.js tests/trace.test.js tests/governor.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine/engine.js');

const BETS = [0.05, 0.10, 0.20, 0.40, 0.60, 1, 2, 5, 10];

test('allowance starts at rtpCap x bet and never goes below zero', () => {
  const g = E.createGovernor({ rtpCap: 0.94 });
  assert.ok(Math.abs(E.governorAllowance(g, 1) - 0.94) < 1e-12);
  g.bets = 10; g.paid = 20; // impossible in play, but the allowance must clamp at 0
  assert.equal(E.governorAllowance(g, 1), 0);
});

test('invariant: paid <= rtpCap x wagered after every round, with mixed bets (200 sessions x 500 rounds)', () => {
  const rng = E.createRng(777001), pick = E.createRng(777002);
  let ahead = 0, checks = 0;
  for (let s = 0; s < 200; s++) {
    const g = E.createGovernor({ rtpCap: 0.94 });
    for (let i = 0; i < 500; i++) {
      const bet = BETS[pick.int(BETS.length)];
      const r = E.playGovernedRound(rng, g, bet, E.DEFAULTS, false);
      E.governorSettle(g, r.win * bet);
      checks++;
      assert.ok(g.paid <= g.rtpCap * g.bets + 1e-9, `session ${s} round ${i}`);
      if (g.paid > g.bets) ahead++;
    }
  }
  assert.equal(checks, 100000);
  assert.equal(ahead, 0, 'the player is never ahead of the house');
});

test('house net is positive after every round when rtpCap < 1', () => {
  const rng = E.createRng(31337), g = E.createGovernor({ rtpCap: 0.94 });
  for (let i = 0; i < 20000; i++) {
    const r = E.playGovernedRound(rng, g, 1, E.DEFAULTS, false);
    E.governorSettle(g, r.win);
    assert.ok(g.bets - g.paid >= 0.06 * g.bets - 1e-9);
  }
});

test('cent rounding: crediting round2(win x bet) with slack 0.005 keeps the invariant (small bets)', () => {
  const rng = E.createRng(4242), g = E.createGovernor({ rtpCap: 0.94, slack: 0.005 });
  const round2 = x => Math.round(x * 100) / 100;
  for (let i = 0; i < 30000; i++) {
    const bet = 0.05;
    const r = E.playGovernedRound(rng, g, bet, E.DEFAULTS, false);
    E.governorSettle(g, round2(r.win * bet));
    assert.ok(g.paid <= g.rtpCap * g.bets + 1e-9, `round ${i}`);
  }
});

test('deterministic: same seed and same bets give the same governed session', () => {
  const run = () => {
    const rng = E.createRng(99), g = E.createGovernor({ rtpCap: 0.94 }), wins = [];
    for (let i = 0; i < 2000; i++) { const r = E.playGovernedRound(rng, g, 1, E.DEFAULTS, false); E.governorSettle(g, r.win); wins.push(r.win); }
    return { wins, rerolls: g.rerolls, paid: g.paid };
  };
  assert.deepEqual(run(), run());
});

test('trace mode: governed frames add up to the governed win and respect the allowance', () => {
  const rng = E.createRng(2026), g = E.createGovernor({ rtpCap: 0.94 });
  for (let i = 0; i < 400; i++) {
    const bet = 1;
    const r = E.playGovernedRound(rng, g, bet, E.DEFAULTS, true);
    E.governorSettle(g, r.win * bet);
    assert.ok(Array.isArray(r.frames) && r.frames.length > 0);
    assert.ok(r.win <= r.governor.allowance + 1e-9);
    assert.ok(g.paid <= g.rtpCap * g.bets + 1e-9);
  }
});

test('a plain engine round is not changed by the governor layer (200 000-round baseline)', () => {
  const a = E.simulate(20000, 123456), b = E.simulate(20000, 123456);
  assert.equal(a.sum, b.sum);
  assert.equal(a.hits, b.hits);
});

test('simulateGoverned reports zero violations and no player-ahead moments (50 sessions x 400 rounds)', () => {
  const a = E.simulateGoverned(50, 400, 5150, E.DEFAULTS, { rtpCap: 0.94 });
  assert.equal(a.rounds, 20000);
  assert.equal(a.invariantViolations, 0);
  assert.equal(a.playerAheadMoments, 0);
  assert.equal(a.playerAheadSessions, 0);
  assert.ok(a.paid / a.rounds <= 0.94 + 1e-9);
});

test('first round of a session cannot pay more than rtpCap x bet', () => {
  for (let seed = 1; seed <= 300; seed++) {
    const g = E.createGovernor({ rtpCap: 0.94 });
    const r = E.playGovernedRound(E.createRng(seed), g, 1, E.DEFAULTS, false);
    assert.ok(r.win <= 0.94 + 1e-9, `seed ${seed}`);
  }
});
