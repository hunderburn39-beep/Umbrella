/* Reactor Rush V5.0 — motor matemático (sem DOM, sem áudio).
 * Referência de regras: Reactoonz 2 (Play'n GO), segundo fontes secundárias.
 * O regulamento oficial do PokerStars NÃO foi acessível durante o desenvolvimento;
 * ver REPORT-V5.0.md para o que está confirmado e o que é interpretação própria.
 * Créditos exclusivamente virtuais (Free Play). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.RREngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var N = 7, CELLS = 49, MIN_CLUSTER = 5;

  /* Símbolos 0..3 = "olho único" (baixos), 4..7 = "dois olhos" (altos).
   * Ordem do índice: 0 amarelo, 1 verde1, 2 vermelho, 3 roxo, 4 azul, 5 laranja, 6 verde2, 7 rosa. */
  var SYMBOLS = [
    { id: 0, name: 'Amarelo', eyes: 1 }, { id: 1, name: 'Verde', eyes: 1 },
    { id: 2, name: 'Vermelho', eyes: 1 }, { id: 3, name: 'Roxo', eyes: 1 },
    { id: 4, name: 'Azul', eyes: 2 }, { id: 5, name: 'Laranja', eyes: 2 },
    { id: 6, name: 'Verde-2', eyes: 2 }, { id: 7, name: 'Rosa', eyes: 2 }
  ];

  /* Tabela de prémios (multiplicadores da aposta) — de fontes secundárias (casinorange.com,
   * allslotsonline.casino), concordantes entre si. Escalões: 5,6,7,8,9,10-11,12-14,15+. NÃO é o regulamento oficial. */
  var PAY = [
    /* tamanho:   5     6     7    8    9   10-11 12-14 15+ */
    /* 0 */ [0.10, 0.15, 0.20, 0.30, 0.60, 0.80, 1, 3],
    /* 1 */ [0.10, 0.15, 0.20, 0.30, 0.60, 0.80, 1, 3],
    /* 2 */ [0.15, 0.20, 0.40, 0.60, 0.80, 1, 3, 10],
    /* 3 */ [0.15, 0.20, 0.40, 0.60, 0.80, 1, 3, 10],
    /* 4 */ [0.50, 0.70, 1, 1.5, 2, 3, 6, 60],
    /* 5 */ [0.60, 0.80, 1, 2, 3, 5, 10, 100],
    /* 6 */ [0.80, 1, 2, 3, 4, 10, 20, 200],
    /* 7 */ [1, 2, 3, 5, 8, 20, 50, 500]
  ];
  var TIER_LABELS = ['5', '6', '7', '8', '9', '10-11', '12-14', '15+'];
  function tier(size) {
    if (size >= 15) return 7; if (size >= 12) return 6; if (size >= 10) return 5; return size - 5;
  }
  function clusterPay(type, size) { return PAY[type][tier(size)]; }

  /* Parâmetros de reatores. Limiares 55/85/110/135 de fontes secundárias. */
  var CFG = {
    weights: [38.8, 38.8, 31.8, 31.8, 15.6, 13.6, 8.9, 6.3],   // calibrado com o simulador (skew 1.221 sobre pesos-base 20,20,17,17,9.5,8.5,6,4.5)
    unchargedChance: 0.03,           // prob. por célula nova (cascatas) — calibrado
    quantumLevels: [55, 85, 110, 135],
    fluctNeeded: 11,                  // símbolos fluctuantes premiados para encher o Fluctometer
    fluctWilds: [1, 3],               // 1–3 Electric Wilds quando o Fluctometer enche
    maxWin: 5000,
    maxCascades: 80
  };

  /* PRNG reproduzível (mulberry32) */
  function makeRng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a; t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* Tipos de célula: kind
   * 'n' normal (t = 0..7) | 'u' wild não carregado | 'e' Electric Wild
   * 'g1' Energoon 1×1 | 'g2' Energoon 2×2 | 'G3','G2','G1' Gargantoon 3×3 / 2×2 / 1×1 */
  function isWild(c) { return c.k !== 'n'; }

  function Spin(rng, cfg) {
    cfg = cfg || CFG;
    var cum = [], s = 0, i;
    for (i = 0; i < 8; i++) { s += cfg.weights[i]; cum.push(s); }
    function randType() { var r = rng() * s; for (var j = 0; j < 8; j++) if (r < cum[j]) return j; return 7; }
    function newCell(allowU) {
      if (allowU && rng() < cfg.unchargedChance) return { k: 'u', t: -1, gid: 0 };
      return { k: 'n', t: randType(), gid: 0 };
    }
    var gidSeq = 0;
    var grid = new Array(CELLS);
    for (i = 0; i < CELLS; i++) grid[i] = newCell(false);
    if (cfg.initialGrid) for (i = 0; i < CELLS; i++) { var ig = cfg.initialGrid[i]; grid[i] = { k: ig.k || 'n', t: ig.k && ig.k !== 'n' ? -1 : ig.t, gid: 0 }; }
    var fluct = cfg.fluct !== undefined ? cfg.fluct : Math.floor(rng() * 4);
    var st = {
      fluct: fluct, fluctCount: 0, fluctFull: 0,
      charge: 0, level: 0, mult: 1, garg: false,
      total: 0, cascades: 0, events: [], counts: { clusters: 0, electric: 0, energoon1: 0, energoon2: 0, garg: 0, pairExp: 0, overload: 0, fluctFill: 0, uncharged: 0 },
      maxCluster: 0, steps: [], frames: [], pendingSpawns: []
    };

    var TRACE = !!cfg.trace;
    function snap() { var o = new Array(CELLS); for (var q = 0; q < CELLS; q++) { var c = grid[q]; o[q] = c ? { k: c.k, t: c.t, gid: c.gid || 0, size: c.size || 1 } : null; } return o; }
    function frame(type, extra) { if (!TRACE) return; var f = extra || {}; f.type = type; f.grid = snap(); f.charge = st.charge; f.level = st.level; f.mult = st.mult; f.fluctCount = st.fluctCount; f.total = st.total; f.garg = st.garg; st.frames.push(f); }
    function idx(r, c) { return r * N + c; }
    function nbrs(p) {
      var r = (p / N) | 0, c = p % N, o = [];
      if (r > 0) o.push(p - N); if (r < N - 1) o.push(p + N); if (c > 0) o.push(p - 1); if (c < N - 1) o.push(p + 1);
      return o;
    }

    function findClusters() {
      var out = [];
      for (var t = 0; t < 8; t++) {
        var seen = new Uint8Array(CELLS);
        for (var p = 0; p < CELLS; p++) {
          var cp = grid[p];
          if (seen[p] || cp.k !== 'n' || cp.t !== t) continue;
          var stack = [p], cells = [], wildSeen = {}; seen[p] = 1;
          while (stack.length) {
            var q = stack.pop(); cells.push(q);
            var nb = nbrs(q);
            for (var z = 0; z < nb.length; z++) {
              var m = nb[z]; if (seen[m]) continue;
              var cm = grid[m];
              if ((cm.k === 'n' && cm.t === t) || (cm.k !== 'n' && cm.k !== 'u')) {
                if (cm.k !== 'n') { /* wild partilhado: pode pertencer a vários grupos */
                  if (wildSeen[m]) continue; wildSeen[m] = 1;
                }
                seen[m] = cm.k === 'n' ? 1 : seen[m]; stack.push(m);
              }
            }
          }
          if (cells.length >= MIN_CLUSTER) out.push({ type: t, cells: cells });
        }
      }
      return out;
    }

    /* Aplica gravidade por colunas; células ancoradas (gigantes 2×2/3×3) bloqueiam a queda.
     * Lacunas acima são preenchidas por novos símbolos; lacunas abaixo de âncoras também (simplificação documentada). */
    function gravityAndRefill(allowU) {
      for (var c = 0; c < N; c++) {
        var segStart = 0;
        for (var r = 0; r <= N; r++) {
          var anchored = r < N && grid[idx(r, c)] && grid[idx(r, c)].anchor;
          if (r === N || anchored) {
            var segEnd = r - 1;
            if (segEnd >= segStart) {
              var keep = [];
              for (var rr = segEnd; rr >= segStart; rr--) { var cell = grid[idx(rr, c)]; if (cell) keep.push(cell); }
              var w = segEnd;
              for (var k = 0; k < keep.length; k++) grid[idx(w--, c)] = keep[k];
              for (; w >= segStart; w--) { var nc = newCell(allowU); if (nc.k === 'u') st.counts.uncharged++; grid[idx(w, c)] = nc; }
            }
            segStart = r + 1;
          }
        }
      }
    }

    function placeGiants(kind, size, count) {
      for (var n = 0; n < count; n++) {
        var span = N - size + 1, total = span * span, start = Math.floor(rng() * total), found = -1, a, b, g;
        for (var k = 0; k < total && found < 0; k++) {
          var pos = (start + k) % total, r0 = (pos / span) | 0, c0 = pos % span, ok = true;
          for (a = 0; a < size && ok; a++) for (b = 0; b < size; b++) { g = grid[idx(r0 + a, c0 + b)]; if (g.anchor || g.k === 'e' || g.k === 'G1' || g.k === 'g1') { ok = false; break; } }
          if (ok) found = pos;
        }
        if (found < 0) continue;               // sem espaço livre: a peça não é colocada (nunca sobrepõe)
        var r = (found / span) | 0, c = found % span;
        gidSeq++;
        for (a = 0; a < size; a++) for (b = 0; b < size; b++) {
          grid[idx(r + a, c + b)] = { k: kind, t: -1, gid: gidSeq, size: size, anchor: size > 1, oy: r, ox: c };
        }
        st.steps.push({ type: 'giant', kind: kind, size: size, r: r, c: c });
      }
    }

    function checkLevels() {
      var L = cfg.quantumLevels, spawned = [];
      while (st.level < 4 && st.charge >= L[st.level]) {
        st.level++;
        st.events.push('level' + st.level);
        if (st.level === 1) { st.counts.energoon1++; spawned.push({ kind: 'g1', size: 1, count: 4 }); }
        else if (st.level === 2) { st.counts.energoon2++; spawned.push({ kind: 'g2', size: 2, count: 1 }); }
        else if (st.level === 3) { st.counts.garg++; st.garg = true; spawned.push({ kind: 'G3', size: 3, count: 1 }); }
        else if (st.level === 4) { st.mult = 2; st.counts.overload++; }
      }
      return spawned;
    }

    function addElectricWilds(n, preferCells) {
      var added = 0, tries = 0;
      while (added < n && tries < 200) {
        tries++;
        var p = Math.floor(rng() * CELLS), cp = grid[p];
        if (cp.k === 'n') { grid[p] = { k: 'e', t: -1, gid: 0 }; added++; st.counts.electric++; }
      }
    }

    /* Fase de ganhos: devolve true se houve prémios */
    function resolveWins(clusters) {
      var win = 0, remove = {}, vacated = [], chargeGain = 0, fluctHits = 0;
      var giantHit = {}, electricInvolved = false;
      var details = [];
      for (var i = 0; i < clusters.length; i++) {
        var cl = clusters[i], hasWild = false, nonWild = 0;
        for (var j = 0; j < cl.cells.length; j++) {
          var cp = grid[cl.cells[j]];
          if (cp.k === 'n') nonWild++; else { hasWild = true; if (cp.gid) giantHit[cp.gid] = cp; }
        }
        var pay = clusterPay(cl.type, cl.cells.length) * st.mult;
        win += pay; st.counts.clusters++;
        if (cl.cells.length > st.maxCluster) st.maxCluster = cl.cells.length;
        details.push({ type: cl.type, size: cl.cells.length, pay: pay, cells: cl.cells.slice(), wild: hasWild });
        if (hasWild && st.level <= 4) chargeGain += nonWild;
        if (cl.type === st.fluct) { fluctHits += nonWild; }
        for (var j2 = 0; j2 < cl.cells.length; j2++) {
          var cc = grid[cl.cells[j2]];
          remove[cl.cells[j2]] = 1;
        }
        if (cl.type === st.fluct && !st.garg) vacated.push(cl.cells[0]);
      }
      /* Uncharged adjacentes a ganhos tornam-se Electric */
      var toElectric = [];
      for (var p in remove) { var nb = nbrs(+p); for (var z = 0; z < nb.length; z++) if (grid[nb[z]].k === 'u') toElectric.push(nb[z]); }
      st.lastWinStep = { type: 'win', clusters: details, win: win };
      st.steps.push(st.lastWinStep);
      st.total += win;
      st.charge += chargeGain;
      /* Remoção: normais e wilds não gigantes saem; gigantes transformam-se */
      var splits = [];
      for (var key in remove) {
        var k = +key, cell = grid[k];
        if (cell.k === 'G3' || cell.k === 'G2') { continue; } // tratados abaixo
        grid[k] = null;
      }
      var gk = Object.keys(giantHit);
      for (var g = 0; g < gk.length; g++) {
        var gc = giantHit[gk[g]];
        if (gc.k === 'G3') splits.push({ from: 'G3', oy: gc.oy, ox: gc.ox });
        else if (gc.k === 'G2') splits.push({ from: 'G2', oy: gc.oy, ox: gc.ox });
      }
      /* Peça gigante atingida: limpa a área e agenda as divisões (colocadas após o preenchimento) */
      for (var s2 = 0; s2 < splits.length; s2++) {
        var sp = splits[s2], sz = sp.from === 'G3' ? 3 : 2;
        for (var a = 0; a < sz; a++) for (var b = 0; b < sz; b++) grid[idx(sp.oy + a, sp.ox + b)] = null;
        if (sp.from === 'G3') { st.pendingSpawns.push({ kind: 'G2', size: 2, count: 2 }); st.steps.push({ type: 'split', from: 'G3', to: 'G2' }); }
        else { st.pendingSpawns.push({ kind: 'G1', size: 1, count: 9 }); st.steps.push({ type: 'split', from: 'G2', to: 'G1' }); }
      }
      /* Fluctometer: contar símbolos fluctuantes premiados; células vagas → Electric Wild */
      if (!st.garg) {
        st.fluctCount += fluctHits;
        for (var v = 0; v < vacated.length; v++) { var vp = vacated[v]; if (grid[vp] === null) { grid[vp] = { k: 'e', t: -1, gid: 0 }; st.counts.electric++; } }
        while (st.fluctCount >= cfg.fluctNeeded) {
          st.fluctCount -= cfg.fluctNeeded; st.counts.fluctFill++;
          st.pendingFluct = (st.pendingFluct || 0) + (cfg.fluctWilds[0] + Math.floor(rng() * (cfg.fluctWilds[1] - cfg.fluctWilds[0] + 1)));
        }
      }
      for (var te = 0; te < toElectric.length; te++) { var gp = grid[toElectric[te]]; if (gp && gp.k === 'u') { grid[toElectric[te]] = { k: 'e', t: -1, gid: 0 }; st.counts.electric++; } }
      return win;
    }

    function wildPairExplosion() {
      var wl = [];
      for (var p = 0; p < CELLS; p++) if (grid[p] && (grid[p].k === 'e')) wl.push(p);
      if (wl.length < 2) return false;
      var any = false, kill = {};
      for (var i = 0; i < wl.length; i++) for (var j = i + 1; j < wl.length; j++) {
        var a = wl[i], b = wl[j], ar = (a / N) | 0, ac = a % N, br = (b / N) | 0, bc = b % N;
        var adjacent = Math.abs(ar - br) + Math.abs(ac - bc) === 1;
        if (adjacent) { for (var q = 0; q < CELLS; q++) if (grid[q].k === 'n' || grid[q].k === 'u') kill[q] = 1; }
        else {
          var r0 = Math.min(ar, br), r1 = Math.max(ar, br), c0 = Math.min(ac, bc), c1 = Math.max(ac, bc);
          for (var r = Math.max(0, r0 - 1); r <= Math.min(N - 1, r1 + 1); r++) for (var c = Math.max(0, c0 - 1); c <= Math.min(N - 1, c1 + 1); c++) {
            var cp = grid[idx(r, c)]; if (cp.k === 'n' || cp.k === 'u') kill[idx(r, c)] = 1;
          }
        }
      }
      var keys = Object.keys(kill);
      if (!keys.length) return false;
      var ch = 0;
      for (var k = 0; k < keys.length; k++) { if (grid[+keys[k]].k === 'n') ch++; grid[+keys[k]] = null; }
      st.charge += ch;           // fontes: remoções não pagam mas carregam o Quantumeter (ver relatório: ambíguo)
      st.counts.pairExp++;
      st.steps.push({ type: 'explosion', removed: keys.length });
      /* Os Electric Wilds mantêm-se em campo */
      return true;
    }

    /* ---- Ciclo principal da ronda ---- */
    var guard = 0;
    frame('start', { fluct: st.fluct });
    for (;;) {
      guard++;
      var clusters = findClusters();
      if (clusters.length) {
        st.cascades++;
        var preWin = TRACE ? snap() : null, winBefore = st.total, lvBefore = st.level;
        resolveWins(clusters);
        if (TRACE) { var last = st.lastWinStep; var f0 = { type: 'win', grid: preWin, clusters: last.clusters, win: last.win, total: st.total, charge: st.charge, level: st.level, mult: st.mult, fluctCount: st.fluctCount, garg: st.garg, cascade: st.cascades, splits: [] }; st.frames.push(f0); }
        var spawn = checkLevels();
        if (TRACE && st.level !== lvBefore) st.frames.push({ type: 'level', level: st.level, from: lvBefore, grid: preWin, charge: st.charge, mult: st.mult });
        gravityAndRefill(true);
        if (st.pendingFluct) { addElectricWilds(st.pendingFluct); st.pendingFluct = 0; }
        if (st.pendingSpawns.length) { spawn = st.pendingSpawns.concat(spawn); st.pendingSpawns = []; }
        for (var q = 0; q < spawn.length; q++) placeGiants(spawn[q].kind, spawn[q].size, spawn[q].count);
        frame('settle', { cascade: st.cascades, spawn: spawn.map(function (x) { return x.kind; }) });
        if (st.cascades >= cfg.maxCascades || st.total >= cfg.maxWin) break;
        continue;
      }
      if (wildPairExplosion()) {
        frame('explosion', { removed: st.steps[st.steps.length - 1].removed });
        var sp2 = checkLevels();
        gravityAndRefill(true);
        for (var q2 = 0; q2 < sp2.length; q2++) placeGiants(sp2[q2].kind, sp2[q2].size, sp2[q2].count);
        frame('settle', { cascade: st.cascades, spawn: sp2.map(function (x) { return x.kind; }), afterExplosion: true });
        continue;
      }
      break;
    }
    if (st.total > cfg.maxWin) st.total = cfg.maxWin;
    return st;
  }

  return {
    N: N, CELLS: CELLS, MIN_CLUSTER: MIN_CLUSTER, SYMBOLS: SYMBOLS, PAY: PAY, TIER_LABELS: TIER_LABELS,
    CFG: CFG, tier: tier, clusterPay: clusterPay, makeRng: makeRng, spin: Spin
  };
});
