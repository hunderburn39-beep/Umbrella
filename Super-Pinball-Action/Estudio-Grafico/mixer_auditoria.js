/* Super Pinball Action — STATIC COMPOSITION AUDIT, NOT THE ARCADE MIXER.
 * Compare the ROM-derived stills (FG, combined, mixed) only where a priority-1
 * sprite actually overlaps. RGB differences indicate potential blend areas.
 * No claim is made that equality proves an opaque tile (equal colours can occur).
 * Works in browsers and can be exercised in Node without DOM dependencies.
 */
(function(root){
 "use strict";
 function auditOverlap(fg,combined,mixed,sprite){
  const n=fg.width*fg.height;
  if(!n||[combined,mixed,sprite].some(x=>x.width!==fg.width||x.height!==fg.height)||
     [fg,combined,mixed,sprite].some(x=>!x.data||x.data.length!==n*4)){
   throw new Error("Incompatible 4-channel composition buffers");
  }
  const rgba=new Uint8ClampedArray(n*4);
  let candidate=0,overlap=0,spritePixels=0;
  for(let i=0;i<n;i++){
   const p=i*4;
   if(!sprite.data[p+3])continue;
   spritePixels++;
   if(!fg.data[p+3])continue;
   const differing=mixed.data[p]!==combined.data[p]||
      mixed.data[p+1]!==combined.data[p+1]||
      mixed.data[p+2]!==combined.data[p+2];
   if(!differing)continue;
   candidate++;
   rgba[p]=255;rgba[p+1]=42;rgba[p+2]=180;rgba[p+3]=186;
   overlap++;
  }
  return {rgba,potentialBlendPixels:candidate,overlapPixels:overlap,spritePixels,
    caveat:"Diferença RGB identifica apenas possíveis zonas de mistura; não substitui os índices de paleta ou os atributos FG da ROM."};
 }
 root.SpaMixerAudit=Object.freeze({auditOverlap});
})(globalThis);
