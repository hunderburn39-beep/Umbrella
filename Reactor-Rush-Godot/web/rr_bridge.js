/* Reactor Rush V5.1 — bridge between the Godot Web export and the validated engine (engine.js).
   Same rules as Reactor-Rush/index.html: governed rounds with the house reserve (rtpCap 0.94, slack 0.005),
   win credited as round2(win x bet) and settled on the reserve. Godot only draws what this returns. */
(function () {
  'use strict';
  var E = window.RREngine, rng = null, gov = null;
  function newSeed() { var a = new Uint32Array(1); if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(a); else a[0] = Math.random() * 4294967296; return a[0] >>> 0; }
  function cell(x) { if (!x) return ''; if (x.k === 'n') return 't' + x.t; return x.k; } // 'u' uncharged, 'e' electric, G1-G3/g1-g2 giants
  window.RRG = {
    ready: function () { return !!E; },
    init: function (seed) {
      if (!E) return 'missing';
      rng = E.createRng(seed ? seed >>> 0 : newSeed());
      gov = E.createGovernor({ rtpCap: 0.94, slack: 0.005 });
      return 'ok';
    },
    spin: function (bet) {
      var res = E.playGovernedRound(rng, gov, bet, E.DEFAULTS, true);
      var won = Math.round(res.win * bet * 100) / 100;
      E.governorSettle(gov, won);
      var frames = res.frames.map(function (f) {
        return { type: f.type, grid: f.grid.map(cell), clusters: (f.clusters || []).map(function (c) { return c.cells; }),
          win: f.win || 0, total: f.total || 0, qm: f.qm || 0, level: f.level || 0, fl: f.fl || 0, flMax: f.flMax || 4,
          garg: !!f.garg, ovc: !!f.ovc, spawn: f.spawn || [], reactor: f.reactor || 0, pair: f.pair || [],
          electric: f.electric || [], zap: f.zap || [], fluct: (typeof f.fluct === 'number' ? f.fluct : 0) };
      });
      return JSON.stringify({ win: res.win, credited: won, frames: frames, govPaid: gov.paid, govBets: gov.bets, cap: gov.rtpCap });
    },
  };
})();
