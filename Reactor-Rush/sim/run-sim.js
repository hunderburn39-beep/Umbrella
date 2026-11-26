#!/usr/bin/env node
'use strict';
/*
 * Reproducible Monte-Carlo runner (Free Play, virtual bet = 1). No rendering code involved.
 *
 *   node Reactor-Rush/sim/run-sim.js --rounds 1000000 --seed 20261126 --workers 4 --out Reactor-Rush/sim/results.json
 *   node Reactor-Rush/sim/run-sim.js --calibrate --rounds 400000 --seed 111
 *
 * The work is split in fixed chunks (chunk i uses seed + i * 0x9E3779B1), so the result does not
 * depend on the number of worker processes.
 */
const { fork } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const E = require('../engine/engine.js');

const CHUNK = 50000;

if (process.argv[2] === '--worker') {
  process.on('message', ({ rounds, seed, cfg }) => {
    process.send(E.simulate(rounds, seed >>> 0, Object.assign({}, E.DEFAULTS, cfg)));
    process.exit(0);
  });
} else main();

function arg(name, def) { const i = process.argv.indexOf('--' + name); return i < 0 ? def : process.argv[i + 1]; }

async function main() {
  const rounds = Number(arg('rounds', 1000000)), seed = Number(arg('seed', 20261126)), workers = Math.max(1, Number(arg('workers', 4)));
  const out = arg('out', null), calibrate = process.argv.includes('--calibrate');
  const cfg = calibrate ? { payScale: 1 } : {};
  const jobs = []; for (let done = 0, i = 0; done < rounds; i++) { const n = Math.min(CHUNK, rounds - done); jobs.push({ rounds: n, seed: (seed + Math.imul(i, 0x9E3779B1)) >>> 0, cfg }); done += n; }
  const results = new Array(jobs.length); let next = 0; const t0 = Date.now();
  await Promise.all(Array.from({ length: workers }, async () => {
    while (next < jobs.length) {
      const k = next++;
      results[k] = await new Promise((res, rej) => { const p = fork(__filename, ['--worker']); p.once('message', res); p.once('error', rej); p.send(jobs[k]); });
    }
  }));
  const agg = E.mergeAgg(results), st = E.rtpStats(agg);
  const report = {
    generatedAt: new Date().toISOString(), node: process.version,
    engine: 'Reactor-Rush/engine/engine.js', rounds: agg.n, seed, chunk: CHUNK, workers,
    config: { payScale: Object.assign({}, E.DEFAULTS, cfg).payScale, minCluster: E.DEFAULTS.minCluster, maxWin: E.DEFAULTS.maxWin },
    referenceRtp: 0.962,
    rtp: st.rtp, standardError: st.se, ci95: st.ci95, perRoundSd: st.sd,
    deltaVsReference: st.rtp - 0.962, referenceInsideCi95: st.ci95[0] <= 0.962 && 0.962 <= st.ci95[1],
    hitRate: st.hitRate, maxWin: agg.maxWin, capHits: agg.capHits,
    avgCascades: agg.cascades / agg.n,
    featureRates: {
      fluctometerAwardsPerRound: agg.flAwards / agg.n,
      quantumeterLevels: { L1: agg.qmL[0] / agg.n, L2: agg.qmL[1] / agg.n, L3: agg.qmL[2] / agg.n, L4: agg.qmL[3] / agg.n },
      roundsWithGargantoon: agg.garg / agg.n, gargantoonSplits3to2x2: agg.splits3 / agg.n, gargantoonSplits2to1x1: agg.splits2 / agg.n,
      pairExplosionsPerRound: agg.explosions / agg.n, zapsPerRound: agg.zaps / agg.n, unchargedBecameElectricPerRound: agg.unchargedLit / agg.n,
    },
    winBuckets: agg.buckets,
    elapsedSeconds: (Date.now() - t0) / 1000,
    caveats: [
      'Paytable and several mechanics are interpretations, not the original; see engine/ASSUMPTIONS.md.',
      'The 95% interval is a normal approximation from per-round variance; wins are heavy-tailed, so it may be optimistic.',
      'Agreement or disagreement with 96.20% says nothing about the original game probabilities.',
    ],
  };
  if (calibrate) report.suggestedPayScale = 0.962 / st.rtp;
  console.log(JSON.stringify(report, null, 2));
  if (out) fs.writeFileSync(path.resolve(out), JSON.stringify(report, null, 2) + '\n');
}
