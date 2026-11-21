/* Super Pinball Action audio — experimental hardware-inspired sound core.
 * YM3812: two-operator FM event voice using Web Audio (NOT cycle-accurate OPL2).
 * OKIM6295: hardware ADPCM 4-bit decoder for samples from a user-owned a-u19 ROM.
 * No recordings or ROM binaries included; no assertion of original Z80 sound timing.
 */
(function(root){
"use strict";
const STEPS=[16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552];
const SHIFT=[-1,-1,-1,-1,2,4,6,8];
function decodeOki(bytes,index){
 if(!(bytes instanceof Uint8Array)||index<0||index>=128)throw Error("Invalid OKI sample");
 const i=index*8;
 if(bytes.length<i+6)throw Error("Missing OKI table");
 const start=((bytes[i]<<16)|(bytes[i+1]<<8)|bytes[i+2])&0x3ffff;
 const end=((bytes[i+3]<<16)|(bytes[i+4]<<8)|bytes[i+5])&0x3ffff;
 if(start<0x400||end<start||end>=bytes.length||end-start>0x40000)return null;
 const pcm=new Float32Array((end-start+1)*2);
 let signal=-2,step=0,j=0;
 for(let at=start;at<=end;at++){
  for(const nibble of [bytes[at]>>>4,bytes[at]&15]){
   const st=STEPS[step];
   let diff=(st>>3)+(nibble&1?st>>2:0)+(nibble&2?st>>1:0)+(nibble&4?st:0);
   signal=Math.max(-2048,Math.min(2047,signal+(nibble&8?-diff:diff)));
   step=Math.max(0,Math.min(48,step+SHIFT[nibble&7]));
   pcm[j++]=signal/2048;
  }
 }
 return pcm;
}
function create(){
 let context=null,master=null,enabled=true,okiBytes=null;
 const playing=new Set(),active=[];
 const report=()=>({
  context:context?.state||"desligado",
  ym3812:"FM de 2 operadores — núcleo experimental, sem sequenciador Z80",
  okim6295:okiBytes?"ADPCM da ROM fornecida, 7576 Hz":"aguarda ROM original a-u19",
  volume:enabled
 });
 function start(){
  const AC=root.AudioContext||root.webkitAudioContext;
  if(!AC)throw Error("Web Audio não suportado");
  if(!context){
   context=new AC({latencyHint:"interactive"});
   master=context.createGain();master.gain.value=.32;
   master.connect(context.destination);
  }
  context.resume().catch(()=>{});
  return context;
 }
 function mute(value){enabled=!value;if(master&&context)master.gain.setTargetAtTime(enabled?.32:0,context.currentTime,.02);return report()}
 function fm(frequency=440,duration=.13,timbre="hit",strength=.8){
  if(!enabled)return;
  const c=start(),at=c.currentTime;
  const mod=c.createOscillator(),carrier=c.createOscillator(),index=c.createGain(),envelope=c.createGain();
  const freq=Math.max(65,Math.min(2400,frequency));
  const harsh=timbre==="metal",ratio=harsh?2.01:timbre==="bass"?.5:1.003;
  mod.type="sine";carrier.type="sine";
  mod.frequency.setValueAtTime(freq*ratio,at);carrier.frequency.setValueAtTime(freq,at);
  index.gain.setValueAtTime(freq*(harsh?1.35:timbre==="bass"?.3:.6),at);
  index.gain.exponentialRampToValueAtTime(.001,at+duration);
  mod.connect(index);index.connect(carrier.frequency);
  envelope.gain.setValueAtTime(.0001,at);
  envelope.gain.linearRampToValueAtTime(Math.max(.005,Math.min(1,strength))*.24,at+.008);
  envelope.gain.exponentialRampToValueAtTime(.0001,at+duration);
  carrier.connect(envelope);envelope.connect(master);
  mod.start(at);carrier.start(at);mod.stop(at+duration+.02);carrier.stop(at+duration+.02);
  active.push([mod,carrier]);
  carrier.onended=()=>{mod.disconnect();index.disconnect();carrier.disconnect();envelope.disconnect();};
 }
 function oki(index,volume=.7){
  if(!enabled||!okiBytes)return false;
  const pcm=decodeOki(okiBytes,index);
  if(!pcm)return false;
  const c=start(),buffer=c.createBuffer(1,pcm.length,7576);
  buffer.copyToChannel(pcm,0);
  const source=c.createBufferSource(),gain=c.createGain();
  gain.gain.value=Math.min(1,Math.max(0,volume));
  source.buffer=buffer;source.connect(gain);gain.connect(master);
  playing.add(source);
  source.onended=()=>{source.disconnect();gain.disconnect();playing.delete(source)};
  source.start();return true;
 }
 function event(kind){
  if(!enabled)return;
  // Provisional 2-op FM cues: these are NOT original ROM music or sound commands.
  const specs={start:[392,.3,"metal"],launch:[261,.16,"bass"],flipper:[462,.055,"metal"],
    bumper:[610,.1,"metal"],score:[785,.18,"hit"],drain:[165,.38,"bass"],
    tilt:[110,.35,"metal"],bonus:[990,.25,"hit"]};
  const v=specs[kind];if(v)fm(...v);
  // No made-up OKI sample map: IDs need to be identified against the sound ROM.
 }
 function importOki(bytes){
  if(!(bytes instanceof Uint8Array)||bytes.length<0x20000||bytes.length>0x80000)
   throw Error("ROM OKI inválida — escolher a-u19 (128 ou 256 KiB)");
  let valid=0;
  for(let i=0;i<128;i++)if(decodeOki(bytes,i))valid++;
  if(!valid)throw Error("A ROM não contém uma tabela OKI utilizável");
  okiBytes=bytes;return {valid,size:bytes.length,report:report()};
 }
 function stopAll(){for(const s of playing){try{s.stop()}catch{}}playing.clear()}
 return {start,event,fm,oki,importOki,decodeOki,mute,report,stopAll};
}
root.SpaChips=Object.freeze({create,decodeOki});
})(window);
