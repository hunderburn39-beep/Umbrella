#!/usr/bin/env node
'use strict';
/*
 * Free Play simulation WITH the house reserve (limite rígido). Virtual bet = 1.
 *
 *   node sim/run-governor.js --sessions 4000 --length 1000 --seed 20261129 --out sim/results-governor-len1000-4M.json
 *
 * Sessions are independent (fresh reserve each), so the confidence interval is computed on session RTPs,
 * not on correlated rounds.
 */
const fs = require('node:fs');
const path = require('node:path');
const E = require('../engine/engine.js');

function arg(name, def) { const i = process.argv.indexOf('--' + name); return i < 0 ? def : process.argv[i + 1]; }
const sessions = Number(arg('sessions', 4000)), length = Number(arg('length', 1000)), seed = Number(arg('seed', 20261129));
const rtpCap = Number(arg('cap', 0.94)), out = arg('out', null);

const t0 = Date.now();
const a = E.simulateGoverned(sessions, length, seed, E.DEFAULTS, { rtpCap });
const rtp = a.paid / a.rounds;
const sMean = a.sessRtpSum / sessions;
const sVar = Math.max(0, (a.sessRtpSumSq - sessions * sMean * sMean) / (sessions - 1));
const sSe = Math.sqrt(sVar / sessions);
const rMean = a.paid / a.rounds, rVar = Math.max(0, (a.sumSq - a.rounds * rMean * rMean) / (a.rounds - 1));
const report = {
  generatedAt: new Date().toISOString(), node: process.version,
  engine: 'Reactor-Rush/engine/engine.js (house reserve layer)', mode: 'Free Play, virtual bet = 1',
  sessions, sessionLength: length, rounds: a.rounds, seed, rtpCap, targetRtp: 0.94,
  effectiveRtp: rtp,
  sessionRtp: { mean: sMean, sd: Math.sqrt(sVar), se: sSe, ci95: [sMean - 1.96 * sSe, sMean + 1.96 * sSe], min: a.sessRtpMin, max: a.sessRtpMax },
  deltaVsTarget: rtp - 0.94,
  volatility: { perRoundSdInBets: Math.sqrt(rVar), sessionRtpSd: Math.sqrt(sVar), maxWin: a.maxWin },
  hitRate: a.hits / a.rounds,
  rerollsPerRound: a.rerolls / a.rounds,
  houseGuarantee: {
    invariantViolations: a.invariantViolations,        // rounds where paid > rtpCap x wagered
    playerAheadMoments: a.playerAheadMoments,          // rounds where paid > wagered
    playerAheadSessions: a.playerAheadSessions,        // sessions ending with the player ahead
    houseKeepsAtLeast: 1 - rtpCap,
  },
  winBuckets: a.buckets,
  elapsedSeconds: (Date.now() - t0) / 1000,
  caveats: [
    'Rounds are drawn from the plain engine and rejected when the reserve cannot pay them; outcomes depend on the session balance and are not independent draws.',
    'Effective RTP is bounded above by rtpCap. It is below the cap when the reserve is still empty, especially in short sessions.',
    'The interval uses session RTPs as independent units; it is a normal approximation.',
    'Paytable and several mechanics are interpretations, not the original; see engine/ASSUMPTIONS.md.',
  ],
};
console.log(JSON.stringify(report, null, 2));
if (out) fs.writeFileSync(path.resolve(out), JSON.stringify(report, null, 2) + '\n');
