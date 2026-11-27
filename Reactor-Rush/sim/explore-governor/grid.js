// node grid.js gridfile  -> runs probe.js for each "label|json" line, 2 at a time
const { execFile } = require('node:child_process');
const lines = require('node:fs').readFileSync(process.argv[2], 'utf8').trim().split('\n');
let i = 0; const out = [];
function next() { if (i >= lines.length) return; const [l, j] = [lines[i].split('|')[0], lines[i].slice(lines[i].indexOf('|') + 1)]; i++;
  const p=l.split('@'); execFile('node', [__dirname + '/probe.js', j, l, p[1]||'0.94'], (e, so, se) => { out.push(e ? l + ' ERR ' + se.split('\n').slice(-3).join(' ') : so.trim()); console.log(out[out.length - 1]); next(); }); }
next(); next();
