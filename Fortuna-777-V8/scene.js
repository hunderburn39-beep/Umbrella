/* Fortuna V8: Babylon scene with dimensions from original SlotScene.tsx.
   Only presentation: V7 rules and virtual-credit state stay authoritative. */
(function(){
"use strict";
window.startFortuna3D=function(){
 if(window.fortuna3DStarting)return;window.fortuna3DStarting=true;
 var canvas=document.getElementById("scene3d"),note=document.getElementById("engineNote");
 var B=window.BABYLON,engine,scene;
 function fallback(msg){document.body.classList.remove("real3d");note.textContent="Modo 2D de segurança: "+msg;try{if(engine)engine.dispose()}catch(_){}}
 try{
 if(!B||!B.Engine.isSupported())throw Error("WebGL indisponível");
 engine=new B.Engine(canvas,true,{preserveDrawingBuffer:false,stencil:false,disableWebGL2Support:false});
 engine.setHardwareScalingLevel(Math.max(1,window.devicePixelRatio/1.5));
 scene=new B.Scene(engine);scene.useRightHandedSystem=true;
 scene.clearColor=new B.Color4(.035,.018,.025,1);
 var V=(x,y,z)=>new B.Vector3(x,y,z),C=h=>B.Color3.FromHexString(h);
 var cam=new B.ArcRotateCamera("camera",Math.PI/2-.27,1.36,9,V(0,2.25,0),scene);
 cam.fov=.7;cam.minZ=.1;cam.maxZ=70;
 cam.lowerAlphaLimit=Math.PI/2-.6;cam.upperAlphaLimit=Math.PI/2+.6;
 cam.lowerBetaLimit=1.15;cam.upperBetaLimit=1.57;
 cam.panningSensibility=0;cam.lowerRadiusLimit=cam.upperRadiusLimit=9;
 cam.attachControl(canvas,true);
 var hemi=new B.HemisphericLight("ambient",V(0,1,.5),scene);hemi.intensity=.85;hemi.groundColor=C("#58404b");
 var key=new B.DirectionalLight("key",V(-.5,-1,-1),scene);key.intensity=1.3;
 var rim=new B.PointLight("rim",V(-3,4,4),scene);rim.diffuse=C("#ffcc90");rim.intensity=.8;
 var face=new B.PointLight("face",V(1,3,4),scene);face.intensity=.5;
 function mat(n,color,shine,emit){var m=new B.StandardMaterial(n,scene);m.diffuseColor=C(color);m.specularColor=C(shine?"#ffffff":"#343434");m.specularPower=shine||32;if(emit)m.emissiveColor=C(emit);return m}
 var paint=mat("red lacquer","#8a0f19",96),chrome=mat("chrome","#bfc3c7",128),gold=mat("gold","#d6a844",90),black=mat("black","#0d0b0c",25),red=mat("red","#e3242b",100),amber=mat("amber","#f0a52a",80),paper=mat("paper","#cfc3a6",8),glass=mat("glass","#ffffff",128);glass.alpha=.07;glass.backFaceCulling=false;glass.disableDepthWrite=true;
 function box(n,x,y,z,w,h,d,m,parent){var o=B.MeshBuilder.CreateBox(n,{width:w,height:h,depth:d},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function cylinder(n,x,y,z,d,h,m,parent){var o=B.MeshBuilder.CreateCylinder(n,{diameter:d,height:h,tessellation:24},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function ball(n,x,y,z,d,m,parent){var o=B.MeshBuilder.CreateSphere(n,{diameter:d,segments:12},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function texture(n,w,h,draw){var t=new B.DynamicTexture(n,{width:w,height:h},scene,false);var c=t.getContext();draw(c,w,h);t.update();return t}
 function texmat(n,t,emissive){var m=mat(n,"#ffffff",12);m.diffuseTexture=t;m.backFaceCulling=false;if(emissive){m.emissiveTexture=t;m.emissiveColor=C("#ffffff")}return m}
 function plane(n,x,y,z,w,h,m,parent){var o=B.MeshBuilder.CreatePlane(n,{width:w,height:h,sideOrientation:B.Mesh.DOUBLESIDE},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 var snapshot=window.fortunaState(),step=Math.PI*2/20,cell=2*.8*Math.tan(step/2),reels=[],bulbs=[],lineMeshes=[],coins=[];
 var glyph={CH:"🍒",LE:"🍋",OR:"🍊",GR:"🍇",BE:"🔔",ST:"⭐",SE:"7"},symbols={};
 Object.keys(glyph).forEach(id=>{
 var t=texture("symbol-"+id,256,112,(c,w,h)=>{var g=c.createLinearGradient(0,0,0,h);g.addColorStop(0,"#efe4cc");g.addColorStop(.5,"#fffaf0");g.addColorStop(1,"#efe4cc");c.fillStyle=g;c.fillRect(0,0,w,h);c.textAlign="center";c.textBaseline="middle";if(id==="SE"){c.font="bold 100px Georgia";c.lineWidth=7;c.strokeStyle="#b8862b";c.strokeText("7",w/2,h*.54);c.fillStyle="#c4141a";c.fillText("7",w/2,h*.54)}else{c.font='87px "Apple Color Emoji","Segoe UI Emoji",sans-serif';c.shadowColor="#0004";c.shadowBlur=5;c.fillText(glyph[id],w/2,h*.54)}});symbols[id]=texmat(id,t,false);symbols[id].emissiveColor=C("#55504a");
 });
 box("pedestal",0,.45,0,2.55,.9,1.95,black);
 box("base trim",0,.87,.98,2.55,.05,.025,gold);
 box("lower",0,1.5125,0,2.4,1.225,1.8,paint);
 box("upper",0,3.2625,0,2.4,.375,1.8,paint);
 box("marquee",0,3.925,0,2.4,.95,1.8,paint);
 box("back",0,2.6,-.84,1.95,.95,.12,black);
 [-1,1].forEach(s=>{box("pillar",s*1.0875,2.6,0,.225,.95,1.8,paint);cylinder("edge",s*1.2,2.175,.9,.07,2.55,chrome);box("window vertical",s*1.005,2.6,.92,.06,1.07,.05,chrome)});
 [2.095,3.105].forEach(y=>box("window horizontal",0,y,.92,2.07,.06,.05,chrome));
 [-.32,.32].forEach(x=>box("separator",x,2.6,.2,.05,.95,1.3,black));
 box("upper trim",0,3.4,.91,2.4,.07,.025,gold);
 box("chute",0,1.58,.91,.8,.16,.028,black);
 box("chute trim",0,1.67,.93,.9,.035,.04,chrome);
 box("tray",0,1.285,1.08,1.26,.03,.39,chrome);
 box("tray front",0,1.32,1.28,1.26,.06,.04,chrome);
 [-1,1].forEach(s=>box("tray side",s*.615,1.32,1.08,.03,.06,.39,chrome));
 var deck=box("deck",0,1.925,1.12,2.3,.10,.45,black);deck.rotation.x=.28;
 box("deck lip",0,1.91,1.345,2.3,.06,.025,chrome);
 var marquee=texture("marquee",1024,360,(c,w,h)=>{var g=c.createRadialGradient(w/2,h/2,20,w/2,h/2,w*.6);g.addColorStop(0,"#7a0d16");g.addColorStop(1,"#22040a");c.fillStyle=g;c.fillRect(0,0,w,h);c.save();c.translate(w/2,h*.55);for(let i=0;i<36;i++){c.rotate(Math.PI*2/36);c.fillStyle=i%2?"#ffc85a12":"#0001";c.beginPath();c.moveTo(0,0);c.lineTo(w,-40);c.lineTo(w,40);c.fill()}c.restore();c.textAlign="center";c.textBaseline="middle";c.font="bold 150px Georgia";c.lineWidth=18;c.strokeStyle="#2a0508";c.strokeText("FORTUNA",w/2,h*.4);c.fillStyle="#ffda74";c.fillText("FORTUNA",w/2,h*.4);c.font="bold 92px Georgia";c.fillStyle="#ff4b43";c.fillText("777",w/2,h*.78)});
 plane("title",0,3.93,.913,2.05,.72,texmat("marquee material",marquee,true));
 var bulbA=mat("bulbs A","#ffcf6b",30,"#ffcf6b"),bulbB=mat("bulbs B","#ffcf6b",30,"#ffcf6b");
 for(let i=0;i<=13;i++)for(let y of [3.54,4.32])bulbs.push(ball("bulb",-1.06+2.12*i/13,y,.94,.076,i%2?bulbA:bulbB));
 for(let i=1;i<4;i++)for(let x of [-1.06,1.06])bulbs.push(ball("bulb",x,3.54+.78*i/4,.94,.076,i%2?bulbA:bulbB));
 cylinder("tower base",.84,4.46,0,.18,.13,chrome);var tower=ball("tower",.84,4.57,0,.18,red);
 snapshot.reels.forEach((strip,i)=>{var group=new B.TransformNode("reel"+i,scene);group.position=V([-.64,0,.64][i],2.6,.05);var drum=cylinder("drum",0,0,0,1.552,.568,paper,group);drum.rotation.z=Math.PI/2;
 strip.forEach((id,j)=>{var pivot=new B.TransformNode("cell"+i+"-"+j,scene);pivot.parent=group;pivot.rotation.x=j*step;plane("symbol",0,0,.8,.58,cell,symbols[id],pivot)});
 reels.push(group);
 });
 plane("glass",0,2.6,.906,1.95,.95,glass);
 var lineColors=["#ff3030","#ffc83a","#35d0c0","#5be05e","#ff8a2a"];
 snapshot.paths.forEach((p,i)=>{var row=[.8*Math.sin(step),0,-.8*Math.sin(step)],pts=[V(-.955,2.6+row[p[0]],.944),...p.map((r,j)=>V([-.64,0,.64][j],2.6+row[r],.944)),V(.955,2.6+row[p[2]],.944)];var m=mat("line"+i,lineColors[i],10,lineColors[i]);var tube=B.MeshBuilder.CreateTube("line"+i,{path:pts,radius:.009,tessellation:6},scene);tube.material=m;tube.setEnabled(false);lineMeshes.push(tube)});
 var leverPivot=new B.TransformNode("lever pivot",scene);leverPivot.position=V(1.28,2.02,0);
 var rod=cylinder("lever",0,.48,0,.065,.96,chrome,leverPivot);var knob=ball("lever knob",0,.98,0,.22,red,leverPivot);
 function clickMesh(o,action){o.actionManager=new B.ActionManager(scene);o.actionManager.registerAction(new B.ExecuteCodeAction(B.ActionManager.OnPickTrigger,action))}
 clickMesh(knob,()=>document.getElementById("lever").click());clickMesh(rod,()=>document.getElementById("lever").click());
 [-.65,0,.65].forEach((x,i)=>{cylinder("button rim",x,2,1.15,.27,.04,chrome);var cap=cylinder("button",x,2.035,1.15,.23,.065,i===2?red:amber);clickMesh(cap,()=>document.getElementById(["down","bet","spin"][i]).click())});
 var carpet=texture("carpet",256,256,(c,w,h)=>{c.fillStyle="#2a080e";c.fillRect(0,0,w,h);c.strokeStyle="#8a6a2c";c.lineWidth=3;c.beginPath();c.moveTo(w/2,10);c.lineTo(w-10,h/2);c.lineTo(w/2,h-10);c.lineTo(10,h/2);c.closePath();c.stroke();c.fillStyle="#0d3236";c.beginPath();c.arc(w/2,h/2,34,0,Math.PI*2);c.fill()});carpet.uScale=carpet.vScale=26;carpet.wrapU=carpet.wrapV=B.Texture.WRAP_ADDRESSMODE;
 var floor=B.MeshBuilder.CreateGround("floor",{width:60,height:60},scene);floor.material=texmat("carpet",carpet,false);
 var displayTex=new B.DynamicTexture("display",{width:1024,height:140},scene,false),display=plane("display",0,1.77,.92,1.94,.22,texmat("display",displayTex,true));
 var coinMaterial=mat("coin","#f4c654",110);
 var wasBusy=false,lastDisplay="",ready=false,frames=0,lastTime=performance.now()/1000;
 var glow=new B.GlowLayer("cabinet glow",scene,{mainTextureFixedSize:256,blurKernelSize:24});glow.intensity=.32;
 var flash=new B.PointLight("win flash",V(0,2.6,2.1),scene);flash.diffuse=C("#ffc24a");flash.intensity=0;
 var streak=texture("glass streak",256,128,(c,w,h)=>{var g=c.createLinearGradient(0,0,w,h);[[.18,0],[.26,.38],[.33,0],[.42,0],[.45,.18],[.49,0]].forEach(a=>g.addColorStop(a[0],"rgba(255,255,255,"+a[1]+")"));c.fillStyle=g;c.fillRect(0,0,w,h)});streak.hasAlpha=true;
 var streakMat=texmat("glass reflection",streak,true);streakMat.useAlphaFromDiffuseTexture=true;streakMat.disableDepthWrite=true;plane("glass reflection",0,2.6,.921,1.95,.95,streakMat);
 var shade=texture("window shade",128,256,(c,w,h)=>{var g=c.createLinearGradient(0,0,0,h);[[0,.65],[.16,.18],[.35,0],[.65,0],[.84,.18],[1,.65]].forEach(a=>g.addColorStop(a[0],"rgba(20,12,10,"+a[1]+")"));c.fillStyle=g;c.fillRect(0,0,w,h)});shade.hasAlpha=true;
 var shadeMat=texmat("window shade",shade,false);shadeMat.useAlphaFromDiffuseTexture=true;shadeMat.disableLighting=true;shadeMat.disableDepthWrite=true;plane("window shadow",0,2.6,.899,1.95,.95,shadeMat);
 var markerMats=[],markers=[];snapshot.paths.forEach((p,i)=>{var t=texture("marker"+i,64,64,(c)=>{c.fillStyle=lineColors[i];c.beginPath();c.arc(32,32,29,0,Math.PI*2);c.fill();c.font="bold 40px sans-serif";c.textAlign="center";c.textBaseline="middle";c.fillStyle="#1a0a05";c.fillText(String(i+1),32,35)});t.hasAlpha=true;var m=texmat("marker"+i,t,true);m.useAlphaFromDiffuseTexture=true;markerMats.push(m);for(let side of [-1,1]){var row=p[side<0?0:2],other=snapshot.paths.map((q,k)=>({row:q[side<0?0:2],k})).filter(q=>q.row===row).map(q=>q.k),offset=(other.indexOf(i)-(other.length-1)/2)*.095;var o=plane("line marker",side*(1.09+offset),2.6+[.8*Math.sin(step),0,-.8*Math.sin(step)][row],.944,.084,.084,m);markers.push(o)}});
 var sparkMat=mat("spark","#ffd98a",12,"#ffd98a"),sparks=[];
 for(let i=0;i<90;i++){let o=ball("spark",0,0,0,.025,sparkMat);o.isPickable=false;o.setEnabled(false);sparks.push({o,x:(Math.random()-.5),y:(Math.random()-.5),z:Math.random(),phase:Math.random()*6.28})}
 function spawnCoins(count){return Array.from({length:Math.min(70,Math.max(6,count))},(_,i)=>{var mesh=cylinder("coin",0,1.58,.94,.13,.016,coinMaterial);mesh.setEnabled(false);mesh.isPickable=false;return{mesh,p:[(Math.random()-.5)*.5,1.58,.94],v:[(Math.random()-.5)*1.2,Math.random()*.6,.5+Math.random()],rot:[Math.random()*Math.PI,Math.random()*Math.PI,Math.random()*Math.PI],spin:[(Math.random()-.5)*18,(Math.random()-.5)*10,(Math.random()-.5)*18],delay:i*.05,layer:Math.floor(Math.random()*Math.min(5,1+count/12)),resting:false}})}
 function stepCoins(dt){for(const c of coins){if(c.delay>0){c.delay-=dt;continue}c.mesh.setEnabled(true);if(!c.resting){var rest=1.3+.008+c.layer*.016*.9;c.v[1]-=9.8*1.4*dt;for(let k=0;k<3;k++){c.p[k]+=c.v[k]*dt;c.rot[k]+=c.spin[k]*dt}for(let a of [[0,-.6,.6],[2,.91,1.26]]){let k=a[0],lo=a[1]+.065,hi=a[2]-.065;if(c.p[k]<lo){c.p[k]=lo;c.v[k]=Math.abs(c.v[k])*.4}if(c.p[k]>hi){c.p[k]=hi;c.v[k]=-Math.abs(c.v[k])*.4}}if(c.p[1]<=rest){c.p[1]=rest;if(Math.abs(c.v[1])>.7){c.v[1]=-c.v[1]*.3;c.spin=c.spin.map(x=>x*.5)}else{c.v[1]=0;let f=Math.exp(-7*dt);c.v[0]*=f;c.v[2]*=f;c.rot[0]*=f;c.rot[2]*=f;c.spin=[0,c.spin[1]*f,0];if(Math.hypot(c.v[0],c.v[2])<.02){c.rot[0]=c.rot[2]=0;c.resting=true}}}}c.mesh.position.set(...c.p);c.mesh.rotation.set(...c.rot)}}
 
 function fit(){engine.resize();var ratio=canvas.clientWidth/Math.max(1,canvas.clientHeight);var r=Math.max(7.8,5.2/Math.max(.55,ratio));cam.lowerRadiusLimit=cam.upperRadiusLimit=r;cam.radius=r}
 window.addEventListener("resize",fit);
 canvas.addEventListener("webglcontextlost",function(e){e.preventDefault();fallback("contexto gráfico perdido")});
 scene.executeWhenReady(function(){if(!engine||engine.isDisposed)return;engine.runRenderLoop(function(){try{
 var st=window.fortunaState(),t=performance.now()/1000,dt=Math.min(.05,Math.max(0,t-lastTime));lastTime=t;reels.forEach((r,i)=>r.rotation.x=-st.visual[i]*step);lineMeshes.forEach((o,i)=>o.setEnabled(st.wins.some(w=>w.i===i)));
 bulbA.emissiveColor=C("#ffcf6b").scale(.55+Math.max(0,Math.sin(t*(st.last?14:3.2))));bulbB.emissiveColor=C("#ffcf6b").scale(.55+Math.max(0,-Math.sin(t*(st.last?14:3.2))));
 leverPivot.rotation.x=st.busy?-.55:0;
 var text=st.balance+"  |  "+st.cost+"  |  "+st.last;if(text!==lastDisplay){lastDisplay=text;var c=displayTex.getContext();c.fillStyle="#070303";c.fillRect(0,0,1024,140);[["CRÉDITO",st.balance,6],["APOSTA",st.cost,3],["PRÉMIO",st.last,5]].forEach((a,i)=>{let x=1024/3*i+1024/6;c.textAlign="center";c.fillStyle="#c99a3a";c.font="600 26px sans-serif";c.fillText(a[0],x,34);c.font="bold 74px monospace";c.fillStyle="rgba(255,60,40,.12)";c.fillText("8".repeat(a[2]),x,116);c.fillStyle="#ff4632";c.shadowColor="#ff2a1a";c.shadowBlur=18;c.fillText(String(Math.min(a[1],10**a[2]-1)).padStart(a[2],"0"),x,116);c.shadowBlur=0});displayTex.update()}
 if(wasBusy&&!st.busy&&st.last>0){coins.forEach(c=>c.mesh.dispose());coins=spawnCoins(Math.round(st.last*1.5))}
 stepCoins(dt);
 var won=st.last>0&&!st.busy,big=won&&st.wins.some(w=>{let p=st.paths[w.i];let ids=p.map((r,j)=>st.reels[j][((Math.round(st.visual[j])+r-1)%20+20)%20]);return ids.every(id=>id===ids[0])});
 flash.intensity=big?1.2+.8*Math.sin(t*16):0;
 sparks.forEach((a,i)=>{let on=i<15||won&&(big||i<55);a.o.setEnabled(on);if(on){let upper=i<15;a.o.position.set(a.x*(upper?2.4:big?4:1.95), (upper?4.15:2.6)+a.y*(upper?.65:big?3.9:.95)+.05*Math.sin(t*3+a.phase),.98+a.z*.25);let k=.5+.5*Math.sin(t*5+a.phase);a.o.scaling.setAll(.3+k)}});
 markerMats.forEach((m,i)=>{m.emissiveColor=C(lineColors[i]).scale(st.wins.some(w=>w.i===i)?1+.5*Math.sin(t*10):.6)});
 wasBusy=st.busy;scene.render();if(!ready&&++frames>=2){ready=true;document.body.classList.add("real3d");note.textContent="Babylon.js · 3D";fit()}
 }catch(e){fallback(e.message)}});fit()});
 setTimeout(function(){if(!ready)fallback("motor 3D não iniciou")},14000);
 }catch(e){fallback(e.message)}
};
})();
