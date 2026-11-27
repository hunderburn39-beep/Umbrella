/* Reactor Rush V5.1 — adds the animated reactor art to the QUANTUMETER and FLUCTOMETER panels.
   Only adds decoration nodes (aria-hidden, no pointer events); existing elements and ids are untouched. */
(function () {
  'use strict';
  function el(tag, cls, html) { const e = document.createElement(tag); e.className = cls; e.setAttribute('aria-hidden', 'true'); if (html) e.innerHTML = html; return e; }

  // Panel chamber for the Quantumeter: hex lattice, two counter-rotating containment rings,
  // a breathing core, conduits with flowing light and blinking status lamps.
  const BG1 = `<svg viewBox="0 0 360 210" preserveAspectRatio="xMidYMid slice"><defs>
<pattern id="rqHex" width="18" height="31.2" patternUnits="userSpaceOnUse"><path d="M9 0l9 5.2v10.4L9 20.8 0 15.6V5.2zM9 20.8v10.4" fill="none" stroke="#5b6cff" stroke-width=".6" opacity=".35"/></pattern>
<radialGradient id="rqCoreG"><stop offset="0" stop-color="#9ff6ff" stop-opacity=".55"/><stop offset=".45" stop-color="#6a3dff" stop-opacity=".22"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<linearGradient id="rqPipe" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b3f8f"/><stop offset=".5" stop-color="#1a1d52"/><stop offset="1" stop-color="#0b0d2e"/></linearGradient></defs>
<rect width="360" height="210" fill="url(#rqHex)"/>
<circle class="breath" cx="180" cy="118" r="92" fill="url(#rqCoreG)"/>
<g class="spin"><circle cx="180" cy="118" r="86" fill="none" stroke="#6f7dff" stroke-width="2" stroke-dasharray="14 9 3 9" opacity=".45"/></g>
<g class="spin rev"><circle cx="180" cy="118" r="70" fill="none" stroke="#c070ff" stroke-width="1.2" stroke-dasharray="2 7" opacity=".55"/>
<path d="M180 40v14M180 182v14M102 118h14M244 118h14" stroke="#7ff3ff" stroke-width="2" opacity=".5"/></g>
<rect x="0" y="194" width="360" height="12" rx="6" fill="url(#rqPipe)"/>
<path class="flow" d="M4 200H356" stroke="#7ff3ff" stroke-width="3" stroke-linecap="round" stroke-dasharray="18 382" opacity=".9"/>
<path class="flow slow" d="M356 200H4" stroke="#ff6fd8" stroke-width="2" stroke-linecap="round" stroke-dasharray="10 190" opacity=".7"/>
<rect x="4" y="34" width="10" height="150" rx="5" fill="url(#rqPipe)"/><rect x="346" y="34" width="10" height="150" rx="5" fill="url(#rqPipe)"/>
<path class="flow" d="M9 184V34" stroke="#6dffb0" stroke-width="2.4" stroke-dasharray="12 188" opacity=".8"/>
<path class="flow slow" d="M351 34V184" stroke="#c070ff" stroke-width="2.4" stroke-dasharray="12 188" opacity=".8"/>
<circle class="blink" cx="24" cy="16" r="3" fill="#6dffb0"/><circle class="blink d1" cx="36" cy="16" r="3" fill="#ffe27a"/><circle class="blink d2" cx="336" cy="16" r="3" fill="#ff6fd8"/><circle class="blink" cx="324" cy="16" r="3" fill="#7ff3ff"/></svg>`;

  // Panel chamber for the Fluctometer: circuit traces with travelling pulses and a slow turbine.
  const BG2 = `<svg viewBox="0 0 360 160" preserveAspectRatio="xMidYMid slice"><defs>
<radialGradient id="rqFlG"><stop offset="0" stop-color="#ff6fd8" stop-opacity=".35"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient></defs>
<g fill="none" stroke="#4a54b8" stroke-width="1.2" opacity=".55">
<path d="M0 30H60l14 14H150M210 44h80l14-14h56M0 130H40l12-12h90M218 118h90l12 12h40"/>
<circle cx="150" cy="44" r="3"/><circle cx="210" cy="44" r="3"/><circle cx="142" cy="118" r="3"/><circle cx="218" cy="118" r="3"/></g>
<g fill="none" stroke-linecap="round" stroke-width="2.2">
<path class="flow" d="M0 30H60l14 14H150" stroke="#7ff3ff" stroke-dasharray="14 386"/>
<path class="flow slow" d="M360 30h-56l-14 14h-80" stroke="#c070ff" stroke-dasharray="14 386"/>
<path class="flow slow" d="M0 130H40l12-12h90" stroke="#6dffb0" stroke-dasharray="14 386"/>
<path class="flow" d="M360 130h-40l-12-12h-90" stroke="#ff6fd8" stroke-dasharray="14 386"/></g>
<circle class="breath" cx="180" cy="80" r="70" fill="url(#rqFlG)"/>
<g class="spin"><g fill="none" stroke="#7f6bff" stroke-width="1.4" opacity=".4">
<circle cx="180" cy="80" r="58" stroke-dasharray="20 10"/><path d="M180 22v116M122 80h116M139 39l82 82M221 39l-82 82"/></g></g>
<circle class="blink" cx="12" cy="12" r="2.6" fill="#7ff3ff"/><circle class="blink d2" cx="348" cy="12" r="2.6" fill="#ffe27a"/></svg>`;

  const ARC = `<svg viewBox="0 0 20 100" preserveAspectRatio="none"><polyline points="10,0 5,14 14,27 6,41 13,55 4,69 12,83 9,100"/><polyline points="10,0 15,16 7,30 15,46 6,60 14,74 7,88 10,100" opacity=".7"/></svg>`;
  const POD = `<svg viewBox="0 0 60 40" preserveAspectRatio="xMidYMid meet"><circle class="core" cx="30" cy="20" r="11"/><circle class="ring" cx="30" cy="20" r="16"/><circle class="ring2" cx="30" cy="20" r="19"/></svg>`;

  function decorate() {
    const p1 = document.getElementById('rrP1'), p2 = document.getElementById('rrP2');
    if (!p1 || !p2 || p1.querySelector('.rq-bg')) return;
    p1.insertBefore(el('div', 'rq-bg', BG1), p1.firstChild);
    p2.insertBefore(el('div', 'rq-bg', BG2), p2.firstChild);
    p1.querySelectorAll('.tube').forEach(t => {
      t.appendChild(el('span', 'rq-core'));
      t.appendChild(el('span', 'rq-arc', ARC));
      t.appendChild(el('span', 'rq-glass'));
      t.appendChild(el('span', 'rq-cap top'));
      t.appendChild(el('span', 'rq-cap bot'));
    });
    const fl = p2.querySelector('.rr-fluct');
    if (fl) fl.insertBefore(el('span', 'rq-portal'), fl.firstChild);
    p2.querySelectorAll('.rr-reactors .rx').forEach(x => x.insertBefore(el('span', 'rq-pod', POD), x.firstChild));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', decorate); else decorate();
})();
