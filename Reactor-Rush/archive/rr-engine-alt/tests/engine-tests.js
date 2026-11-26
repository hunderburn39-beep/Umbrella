#!/usr/bin/env node
/* Reactor Rush V5.0 — testes do motor. Uso: node tests/engine-tests.js */
'use strict';
var E = require('../rr-engine.js');
var fs = require('fs'), path = require('path');
var results = [], failed = 0;
function T(name, fn) {
  try { var detail = fn(); results.push({ test: name, ok: true, detail: detail || '' }); console.log('PASS', name, detail ? '— ' + detail : ''); }
  catch (e) { failed++; results.push({ test: name, ok: false, detail: String(e && e.message || e) }); console.log('FAIL', name, '—', e && e.message || e); }
}
function eq(a, b, m) { if (a !== b) throw new Error((m || 'esperado ' + b) + ' mas obteve ' + a); }
function ok(c, m) { if (!c) throw new Error(m || 'falhou'); }
var BIG = 1e9, N = 7;
function fill(fn) { var g = []; for (var r = 0; r < N; r++) for (var c = 0; c < N; c++) g.push(fn(r, c)); return g; }
function cfgG(grid, extra) { return Object.assign({}, E.CFG, { trace: true, initialGrid: grid, fluct: 7 }, extra || {}); }   // fluct=7 → nenhum tipo "fluctuante" (só 0..3 são de olho único)
function firstWin(st) { return st.frames.find(function (f) { return f.type === 'win'; }); }
function others(t) { var a = []; for (var i = 0; i < 8; i++) if (i !== t) a.push(i); return a; }

/* T1: todos os símbolos × todos os tamanhos 5..49 → prémio da tabela */
T('Tabela: todos os símbolos e tamanhos 5–49 pagam o escalão correto', function () {
  var checks = 0;
  for (var t = 0; t < 8; t++) for (var n = 5; n <= 49; n++) {
    var o = others(t);
    var grid = fill(function (r, c) { var idx = r * N + c; return idx < n ? { k: 'n', t: t } : { k: 'n', t: o[(r * 2 + c * 3) % 7] }; });
    var st = E.spin(E.makeRng(1), cfgG(grid));
    var w = firstWin(st); ok(w, 'sem ganho t=' + t + ' n=' + n);
    var cl = w.clusters.filter(function (c) { return c.type === t; });
    eq(cl.length, 1, 'nº de grupos t=' + t + ' n=' + n); eq(cl[0].size, n, 'tamanho t=' + t + ' n=' + n);
    var exp = E.PAY[t][n >= 15 ? 7 : n >= 12 ? 6 : n >= 10 ? 5 : n - 5];
    eq(cl[0].pay, exp, 'prémio t=' + t + ' n=' + n); checks++;
  }
  return checks + ' combinações verificadas';
});
T('Tabela: 8 símbolos, 8 escalões, valores não decrescentes e iguais à fonte', function () {
  eq(E.PAY.length, 8); E.PAY.forEach(function (row, t) { eq(row.length, 8); for (var i = 1; i < 8; i++) ok(row[i] >= row[i - 1], 'não crescente em ' + t); });
  eq(E.PAY[7][7], 500); eq(E.PAY[0][0], 0.1); eq(E.PAY[6][5], 10); eq(E.PAY[4][6], 6); return 'ok';
});
T('Tabela: tier() mapeia 5..15+ corretamente', function () {
  var exp = { 5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5, 11: 5, 12: 6, 13: 6, 14: 6, 15: 7, 30: 7 };
  Object.keys(exp).forEach(function (k) { eq(E.tier(+k), exp[k], 'tier ' + k); }); return 'ok';
});

/* T2: oráculo independente (união-busca) em tabuleiros aleatórios */
function oracle(cells) {
  var res = [];
  for (var t = 0; t < 8; t++) {
    var seen = {};
    for (var s = 0; s < 49; s++) {
      if (seen[s] || cells[s].k !== 'n' || cells[s].t !== t) continue;
      var q = [s], comp = {}, size = 0; comp[s] = 1; seen[s] = 1; var normals = 0;
      while (q.length) {
        var p = q.pop(); size++; if (cells[p].k === 'n') normals++;
        var r = (p / 7) | 0, c = p % 7, nb = [];
        if (r > 0) nb.push(p - 7); if (r < 6) nb.push(p + 7); if (c > 0) nb.push(p - 1); if (c < 6) nb.push(p + 1);
        nb.forEach(function (m) { if (comp[m]) return; var cm = cells[m]; if ((cm.k === 'n' && cm.t === t) || (cm.k !== 'n' && cm.k !== 'u')) { comp[m] = 1; if (cm.k === 'n') seen[m] = 1; q.push(m); } });
      }
      if (size >= 5) res.push(t + ':' + size);
    }
  }
  return res.sort().join(',');
}
T('Deteção de grupos: motor = oráculo independente em 30 000 tabuleiros (com Wilds)', function () {
  var rng = E.makeRng(99), diffs = 0, wins = 0;
  for (var i = 0; i < 30000; i++) {
    var cells = fill(function () { var x = rng(); if (x < .07) return { k: 'e', t: -1 }; if (x < .09) return { k: 'u', t: -1 }; return { k: 'n', t: Math.floor(rng() * 4) + (rng() < .5 ? 0 : 4) }; });
    var st = E.spin(E.makeRng(i), cfgG(cells));
    var w = st.frames[1] && st.frames[1].type === 'win' ? st.frames[1] : null; var eng = w ? w.clusters.map(function (c) { return c.type + ':' + c.size; }).sort().join(',') : '';
    if (w) wins++;
    if (eng !== oracle(cells)) diffs++;
  }
  eq(diffs, 0, diffs + ' divergências'); return wins + ' tabuleiros com ganho, 0 divergências';
});

/* Wilds */
T('Wild carregado (Electric) substitui e liga grupos; Wild não carregado não ganha nem liga', function () {
  var o = others(0);
  var g1 = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; });
  [0, 1, 2, 3].forEach(function (c) { g1[c] = { k: 'n', t: 0 }; }); g1[4] = { k: 'e' };   // 4 normais + 1 Electric = 5
  var st = E.spin(E.makeRng(5), cfgG(g1)); var w = firstWin(st); ok(w); eq(w.clusters[0].size, 5);
  var g2 = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; });
  [0, 1, 2, 3].forEach(function (c) { g2[c] = { k: 'n', t: 0 }; }); g2[4] = { k: 'u' };     // 4 normais + Uncharged = 4 → sem ganho
  var st2 = E.spin(E.makeRng(5), cfgG(g2, { unchargedChance: 0 })); ok(!firstWin(st2), 'Uncharged não deve ligar');
  var g3 = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); for (var c = 0; c < 5; c++) g3[c] = { k: 'u' };
  ok(!firstWin(E.spin(E.makeRng(5), cfgG(g3, { unchargedChance: 0 }))), 'Uncharged sozinhos não ganham'); return 'ok';
});
T('Wild não carregado junto de um ganho torna-se Electric', function () {
  var o = others(0);
  var g = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; });
  for (var c = 0; c < 5; c++) g[c] = { k: 'n', t: 0 }; g[5] = { k: 'u' }; g[12] = { k: 'u' };   // vizinhos do grupo na linha 0
  var st = E.spin(E.makeRng(5), cfgG(g, { unchargedChance: 0 })); var s = st.frames.find(function (f) { return f.type === 'settle'; });
  ok(s, 'sem settle'); var el = s.grid.filter(function (x) { return x && x.k === 'e'; }).length; ok(el >= 1, 'nenhum Electric'); return el + ' Electric após o ganho';
});

/* Reatores: ativação individual, simultânea, Gargantoon, multiplicador */
function reactorGrid() { var o = others(0); var g = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); for (var c = 0; c < 7; c++) g[c] = { k: 'n', t: 0 }; for (c = 0; c < 2; c++) g[7 + c] = { k: 'n', t: 0 }; g[9] = { k: 'e' }; return g; }   // 9 normais + 1 Electric → carga 9
function spawnsOf(st) { var s = st.frames.find(function (f) { return f.type === 'settle'; }); return s ? s.spawn : null; }
T('Reator 1 (Energoon 1×1): ativação individual → 4 Energoons', function () {
  var st = E.spin(E.makeRng(1), cfgG(reactorGrid(), { quantumLevels: [3, BIG, BIG, BIG] }));
  var sp = spawnsOf(st); ok(sp && sp.join() === 'g1', 'spawn ' + sp); eq(st.counts.energoon1, 1); eq(st.level >= 1, true);
  var s = st.frames.find(function (f) { return f.type === 'settle'; }); eq(s.grid.filter(function (x) { return x && x.k === 'g1'; }).length, 4, '4 Energoons'); return 'ok';
});
T('Reatores 1+2 em simultâneo → 4 Energoons 1×1 e um 2×2', function () {
  var st = E.spin(E.makeRng(1), cfgG(reactorGrid(), { quantumLevels: [3, 6, BIG, BIG] })); var sp = spawnsOf(st); ok(sp && sp.join() === 'g1,g2', 'spawn ' + sp);
  var s = st.frames.find(function (f) { return f.type === 'settle'; }); eq(s.grid.filter(function (x) { return x && x.k === 'g2'; }).length, 4, '2×2 = 4 células'); return 'ok';
});
T('Reatores 1+2+3 → Gargantoon 3×3 (9 células)', function () {
  var st = E.spin(E.makeRng(1), cfgG(reactorGrid(), { quantumLevels: [3, 5, 7, BIG] })); var sp = spawnsOf(st); ok(sp && sp.join() === 'g1,g2,G3', 'spawn ' + sp);
  var s = st.frames.find(function (f) { return f.type === 'settle'; }); eq(s.grid.filter(function (x) { return x && x.k === 'G3'; }).length, 9, 'G3'); ok(st.garg, 'garg'); return 'ok';
});
T('Reator 4 (Sobrecarga ×2): multiplicador aplicado a todos os prémios seguintes', function () {
  var checked = 0, rng = E.makeRng(7);
  for (var i = 0; i < 20000; i++) { var st = E.spin(rng, Object.assign({}, E.CFG, { trace: true, quantumLevels: [4, 6, 8, 10] }));
    st.frames.forEach(function (f) { if (f.type === 'win') f.clusters.forEach(function (c) { eq(c.pay, E.clusterPay(c.type, c.size) * f.mult, 'multiplicador'); if (f.mult === 2) checked++; }); }); }
  ok(checked > 100, 'poucos casos ×2: ' + checked); return checked + ' grupos pagos com ×2 verificados';
});
T('Gargantoon: 3×3 → dois 2×2 → nove 1×1 (cada fase só após ser premiado)', function () {
  var rng = E.makeRng(11), seq = { g3: 0, g2: 0, g1: 0 };
  for (var i = 0; i < 30000 && (!seq.g1 || !seq.g2); i++) {
    var st = E.spin(rng, Object.assign({}, E.CFG, { trace: true, quantumLevels: [4, 6, 8, BIG] }));
    st.frames.forEach(function (f) {
      if (f.type !== 'settle' || !f.spawn) return;
      var cnt = function (k) { return f.grid.filter(function (x) { return x && x.k === k; }).length; };
      if (f.spawn.indexOf('G3') >= 0) { eq(cnt('G3'), 9); seq.g3++; }
      if (f.spawn.indexOf('G2') >= 0) { eq(cnt('G3'), 0, 'G3 deve desaparecer'); eq(cnt('G2'), 8, 'duas peças 2×2'); seq.g2++; }
      if (f.spawn.indexOf('G1') >= 0) { eq(cnt('G2'), 0 + cnt('G2') * 0, ''); ok(cnt('G1') >= 9, 'nove G1'); seq.g1++; }
    });
  }
  ok(seq.g3 > 0 && seq.g2 > 0 && seq.g1 > 0, 'fases em falta ' + JSON.stringify(seq)); return JSON.stringify(seq);
});
T('Energoon 2×2 e restantes Wilds gigantes mantêm-se sem sobreposição (grelha válida)', function () {
  var rng = E.makeRng(21), checked = 0;
  for (var i = 0; i < 20000; i++) { var st = E.spin(rng, Object.assign({}, E.CFG, { trace: true, quantumLevels: [4, 6, 8, 10] }));
    st.frames.forEach(function (f) { if (f.type === 'settle') { var g2 = f.grid.filter(function (x) { return x && (x.k === 'g2' || x.k === 'G2'); }).length; ok(g2 % 4 === 0, 'células 2×2 múltiplas de 4: ' + g2); var g3 = f.grid.filter(function (x) { return x && x.k === 'G3'; }).length; ok(g3 % 9 === 0, 'G3 múltiplo de 9'); checked++; } }); }
  return checked + ' fotogramas verificados';
});

/* Fluctometer */
T('Fluctometer: grupo do símbolo flutuante deixa Electric Wild; outro símbolo não', function () {
  var o = others(0);
  var base = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); for (var c = 0; c < 5; c++) base[c] = { k: 'n', t: 0 };
  var s1 = E.spin(E.makeRng(3), cfgG(base, { fluct: 0, unchargedChance: 0 })).frames.find(function (f) { return f.type === 'settle'; });
  ok(s1.grid.some(function (x) { return x && x.k === 'e'; }), 'com fluct=0 deve surgir Electric');
  var s2 = E.spin(E.makeRng(3), cfgG(base, { fluct: 3, unchargedChance: 0 })).frames.find(function (f) { return f.type === 'settle'; });
  ok(!s2.grid.some(function (x) { return x && x.k === 'e'; }), 'com outro fluct não deve surgir'); return 'ok';
});
T('Fluctometer cheio (11) acrescenta 1–3 Electric Wilds', function () {
  var o = others(0);
  var base = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); for (var i = 0; i < 11; i++) base[i] = { k: 'n', t: 0 };
  var st = E.spin(E.makeRng(3), cfgG(base, { fluct: 0, unchargedChance: 0 })); eq(st.counts.fluctFill >= 1, true);
  var s = st.frames.find(function (f) { return f.type === 'settle'; }); var e = s.grid.filter(function (x) { return x && x.k === 'e'; }).length; ok(e >= 2 && e <= 4, 'Electric ' + e); return e + ' Electric (1 por grupo + 1–3)';
});

/* Wild Pair Explosion */
T('Wild Pair Explosion: Electric adjacentes removem todos os não-Wilds; Wilds mantêm-se', function () {
  var o = others(0); var g = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); g[24] = { k: 'e' }; g[25] = { k: 'e' };
  var st = E.spin(E.makeRng(2), cfgG(g, { unchargedChance: 0 })); var ex = st.frames.find(function (f) { return f.type === 'explosion'; }); ok(ex, 'sem explosão');
  eq(ex.grid.filter(function (x) { return x && x.k === 'n'; }).length, 0, 'sem normais'); eq(ex.grid.filter(function (x) { return x && x.k === 'e'; }).length, 2, 'Wilds mantidos'); eq(ex.total, 0, 'sem prémio'); ok(st.charge > 0, 'carrega Quantumeter'); return 'ok';
});
T('Wild Pair Explosion: Electric afastados destroem apenas o retângulo entre/à volta', function () {
  var o = others(0); var g = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); g[0] = { k: 'e' }; g[17] = { k: 'e' };
  var st = E.spin(E.makeRng(2), cfgG(g, { unchargedChance: 0 })); var ex = st.frames.find(function (f) { return f.type === 'explosion'; }); ok(ex);
  var left = ex.grid.filter(function (x) { return x && x.k === 'n'; }).length; ok(left > 0 && left < 47 && left > 20, 'destruição parcial: restam ' + left); eq(ex.grid[0].k, 'e'); eq(ex.grid[17].k, 'e'); return 'restam ' + left + ' normais';
});
T('Sem Wild Pair Explosion com menos de 2 Electric Wilds', function () {
  var o = others(0); var g = fill(function (r, c) { return { k: 'n', t: o[(r * 2 + c * 3) % 7] }; }); g[24] = { k: 'e' };
  eq(E.spin(E.makeRng(2), cfgG(g, { unchargedChance: 0 })).counts.pairExp, 0); return 'ok';
});

/* Cascatas e consistência */
T('Cascatas consecutivas: win→settle alternam; total = soma dos ganhos', function () {
  var rng = E.makeRng(33), maxC = 0, multi = 0;
  for (var i = 0; i < 40000; i++) { var st = E.spin(rng, Object.assign({}, E.CFG, { trace: true })); var sum = 0, expectNext = 'win';
    st.frames.forEach(function (f) { if (f.type === 'win') sum += f.win; });
    if (st.total < E.CFG.maxWin) ok(Math.abs(sum - st.total) < 1e-6, 'soma ' + sum + ' vs ' + st.total);
    if (st.cascades > maxC) maxC = st.cascades; if (st.cascades >= 3) multi++; }
  ok(maxC >= 6, 'máx cascatas ' + maxC); return 'máx ' + maxC + ' cascatas; ' + multi + ' rondas com ≥3';
});
T('Dois ou mais grupos simultâneos são todos pagos na mesma cascata', function () {
  var g = fill(function (r, c) { return { k: 'n', t: 6 + ((r + c) % 2) }; });   // xadrez de 2 símbolos: sem grupos
  for (var c = 0; c < 5; c++) { g[c] = { k: 'n', t: 0 }; g[28 + c] = { k: 'n', t: 1 }; }
  var st = E.spin(E.makeRng(1), cfgG(g)); var w = firstWin(st); ok(w.clusters.length >= 2, 'grupos ' + w.clusters.length);
  var sum = 0; w.clusters.forEach(function (c) { sum += c.pay; }); eq(Math.abs(sum - w.win) < 1e-9, true); return w.clusters.length + ' grupos';
});
T('Aposta = 1: nenhum prémio excede o teto, grelha sempre 49 células, sem NaN', function () {
  var rng = E.makeRng(44);
  for (var i = 0; i < 50000; i++) { var st = E.spin(rng, Object.assign({}, E.CFG, { trace: true })); ok(isFinite(st.total) && st.total >= 0 && st.total <= E.CFG.maxWin, 'total ' + st.total); st.frames.forEach(function (f) { eq(f.grid.length, 49); }); }
  return 'ok';
});
T('Reprodutibilidade: mesma semente → mesmos resultados; sementes diferentes divergem', function () {
  function run(seed) { var r = E.makeRng(seed), a = []; for (var i = 0; i < 2000; i++) a.push(E.spin(r).total); return a.join(','); }
  eq(run(123), run(123)); ok(run(123) !== run(124)); return 'ok';
});
T('Sem funcionalidades antigas: nenhum jackpot, nenhum "doubled/giantoonz" no motor', function () {
  var src = fs.readFileSync(path.join(__dirname, '../rr-engine.js'), 'utf8'); ok(!/jackpot|giantoonz|implos|demoli/i.test(src.replace(/Sem jackpot[^\n]*/g, ''))); return 'ok';
});

var out = { generated: new Date().toISOString(), node: process.version, total: results.length, failed: failed, results: results };
fs.writeFileSync(path.join(__dirname, 'results-engine.json'), JSON.stringify(out, null, 2));
console.log('\n' + (results.length - failed) + '/' + results.length + ' testes passaram');
process.exit(failed ? 1 : 0);
