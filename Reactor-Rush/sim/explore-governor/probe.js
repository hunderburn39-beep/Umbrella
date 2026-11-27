// Quick probe (300k raw rounds; 2000x100 and 300x1000 governed rounds). Exploration only, not a validation.
'use strict';
// usage: node probe.js '<json overrides>' label
const E = require('../../engine/engine.js');
const ov = JSON.parse(process.argv[2]), label = process.argv[3], CAP = Number(process.argv[4] || 0.94);
const cfg = Object.assign({}, E.DEFAULTS, ov);
const raw = E.rtpStats(E.simulate(300000, 9101, cfg));
const g100 = E.simulateGoverned(2000, 100, 9102, cfg, { rtpCap: CAP });
const g1k = E.simulateGoverned(300, 1000, 9103, cfg, { rtpCap: CAP });
const f = x => (100 * x).toFixed(2);
console.log([label, 'raw', f(raw.rtp), 'sd', raw.sd.toFixed(2), 'gov100', f(g100.paid / g100.rounds), 'gov1000', f(g1k.paid / g1k.rounds), 'hit', f(g1k.hits / g1k.rounds), 'rer1k', (g1k.rerolls/g1k.rounds).toFixed(3), 'max1k', g1k.maxWin.toFixed(1), 'viol', g100.invariantViolations + g1k.invariantViolations].join(' '));
