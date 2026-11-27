// Browser test of the Godot Web export (WebGL 2 through SwiftShader). Run by the reactor-rush-godot-web workflow.
import { chromium } from 'playwright';
import fs from 'node:fs';
const URL = process.env.URL || 'http://127.0.0.1:8080/index.html';
const out = process.env.OUT || 'smoke';
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const results = []; let fail = false;
const rec = (name, ok, info) => { results.push({ name, ok, info }); if (!ok) fail = true; console.log((ok ? 'PASS ' : 'FAIL ') + name + ' — ' + JSON.stringify(info)); };
const waitSpin = (page, before) => page.waitForFunction(b => window.__rrg_state.spins > b && !window.__rrg_state.busy, before, { timeout: 90000 }).catch(() => {});
for (const [name, vp] of [['landscape', { width: 1280, height: 720 }], ['portrait', { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport: vp, deviceScaleFactor: 1 });
  const logs = [];
  page.on('console', m => logs.push(m.type() + ': ' + m.text()));
  page.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await page.goto(URL);
  let ready = false;
  try { await page.waitForFunction(() => window.__rrg_state && window.__rrg_state.ready, null, { timeout: 120000 }); ready = true; } catch (e) {}
  rec(name + ': game ready', ready, null);
  if (!ready) { fs.writeFileSync(`${out}/${name}-console.txt`, logs.join('\n')); await page.screenshot({ path: `${out}/${name}-notready.png` }); await page.close(); continue; }
  const st0 = await page.evaluate(() => window.__rrg_state);
  rec(name + ': engine.js connected', st0.engine === true, st0);
  rec(name + ': orientation detected', st0.portrait === (name === 'portrait'), st0.portrait);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${out}/${name}-start.png` });
  const n = name === 'landscape' ? 30 : 5;
  for (let i = 0; i < n; i++) {
    const before = await page.evaluate(() => window.__rrg_state.spins);
    await page.evaluate(() => window.__rrg_spin());
    if (i === 0) { await page.waitForTimeout(1600); await page.screenshot({ path: `${out}/${name}-cascade.png` }); }
    await waitSpin(page, before);
  }
  const st = await page.evaluate(() => window.__rrg_state);
  rec(name + `: ${n} rounds completed`, st.spins >= n, st);
  rec(name + ': house reserve paid <= 94% of wagered', st.govBets > 0 && st.govPaid <= st.cap * st.govBets + 1e-9, st);
  rec(name + ': balance = 1000 - wagered + paid', Math.abs(st.balance - (1000 - st.govBets + st.govPaid)) < 0.011, st);
  if (name === 'landscape') {
    const b0 = st.spins;
    await page.mouse.click(vp.width * (0.8367 + 0.1125 / 2), vp.height * (0.7843 + 0.2 / 2));
    await waitSpin(page, b0);
    const st2 = await page.evaluate(() => window.__rrg_state);
    rec('clicking the spin button plays a round', st2.spins > b0, st2.spins);
  }
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${out}/${name}-end.png` });
  const errs = logs.filter(l => /SCRIPT ERROR|Parse Error|pageerror|USER ERROR|Invalid call|Attempt to call/i.test(l));
  rec(name + ': no script errors in the console', errs.length === 0, errs.slice(0, 8));
  fs.writeFileSync(`${out}/${name}-console.txt`, logs.join('\n'));
  console.log('@@CONSOLE ' + name + '\n' + logs.slice(0, 40).join('\n'));
  await page.close();
}
fs.writeFileSync(`${out}/results.json`, JSON.stringify(results, null, 2));
// Print small JPEG copies of the screenshots into the log (for reviewers who cannot download artifacts).
if (process.env.LOG_SHOTS) {
  const b2 = await chromium.launch();
  const pg = await b2.newPage({ viewport: { width: 960, height: 960 } });
  for (const f of fs.readdirSync(out).filter(f => f.endsWith('.png')).sort()) {
    const data = fs.readFileSync(`${out}/${f}`).toString('base64');
    await pg.setContent(`<html><body style="margin:0;background:#000"><img id="i" src="data:image/png;base64,${data}" style="max-width:960px;max-height:960px;display:block"></body></html>`);
    const box = await pg.locator('#i').boundingBox();
    const jpg = (await pg.locator('#i').screenshot({ type: 'jpeg', quality: 70 })).toString('base64');
    console.log(`@@SHOT ${f} ${Math.round(box.width)}x${Math.round(box.height)} ${jpg.length}`);
    for (let i = 0; i < jpg.length; i += 3000) console.log('@@B64 ' + f + ' ' + jpg.slice(i, i + 3000));
  }
  await b2.close();
}
await browser.close();
console.log(results.filter(r => r.ok).length + ' / ' + results.length + ' passed');
process.exit(fail ? 1 : 0);
