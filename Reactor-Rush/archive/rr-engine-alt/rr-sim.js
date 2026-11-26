#!/usr/bin/env node
/* Reactor Rush V5.0 — simulador independente e reproduzível.
 * Uso: node rr-sim.js [rondas=1000000] [semente=20260101] [saída.json]
 * RTP observado = soma(prémios) / soma(apostas) com aposta fixa 1. */
'use strict';
var E = require('./rr-engine.js');
var fs = require('fs');
var rounds = +process.argv[2] || 1000000, seed = +process.argv[3] || 20260101, out = process.argv[4];
var rng = E.makeRng(seed);
var sum = 0, sum2 = 0, hits = 0, maxWin = 0;
var buckets = [0, 0, 0, 0, 0, 0, 0, 0, 0]; // 0; <1; 1-2; 2-5; 5-10; 10-50; 50-100; 100-500; 500+
var edges = [0, 1, 2, 5, 10, 50, 100, 500];
var feat = { electric: 0, energoon1: 0, energoon2: 0, garg: 0, pairExp: 0, overload: 0, fluctFill: 0, uncharged: 0, clusters: 0, cascades: 0 };
var roundsWith = { electric: 0, energoon1: 0, energoon2: 0, garg: 0, pairExp: 0, overload: 0, fluctFill: 0 };
var maxCl = 0, t0 = Date.now();
for (var i = 0; i < rounds; i++) {
  var s = E.spin(rng);
  var w = s.total;
  sum += w; sum2 += w * w;
  if (w > 0) hits++;
  if (w > maxWin) maxWin = w;
  var b = 0; if (w > 0) { b = 1; while (b < 8 && w >= edges[b]) b++; } buckets[Math.min(b, 8)]++;
  for (var k in feat) { if (k === 'cascades') feat[k] += s.cascades; else feat[k] += s.counts[k] || 0; }
  for (var k2 in roundsWith) if (s.counts[k2] > 0) roundsWith[k2]++;
  if (s.maxCluster > maxCl) maxCl = s.maxCluster;
}
var mean = sum / rounds, variance = sum2 / rounds - mean * mean, sd = Math.sqrt(variance), se = sd / Math.sqrt(rounds);
var res = {
  rounds: rounds, seed: seed, seconds: (Date.now() - t0) / 1000,
  rtpObserved: mean, ci95: [mean - 1.96 * se, mean + 1.96 * se], stdDev: sd, volatilityIndex: sd,
  hitFrequency: hits / rounds, maxWinObserved: maxWin, largestCluster: maxCl,
  distribution: { 'sem prémio': buckets[0], '0-1x (excl.0)': buckets[1], '1-2x': buckets[2], '2-5x': buckets[3], '5-10x': buckets[4], '10-50x': buckets[5], '50-100x': buckets[6], '100-500x': buckets[7], '500x+': buckets[8] },
  featureTotals: feat, roundsWithFeature: roundsWith,
  roundsWithFeaturePct: Object.keys(roundsWith).reduce(function (o, k) { o[k] = roundsWith[k] / rounds; return o; }, {})
};
console.log(JSON.stringify(res, null, 2));
if (out) fs.writeFileSync(out, JSON.stringify(res, null, 2));
