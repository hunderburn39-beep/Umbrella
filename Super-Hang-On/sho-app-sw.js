'use strict';
const CACHE='sho-pwa-shell-v232';
const urls=['app.html','sho-app.webmanifest','sho-app-icon.png','sho-app-icon.svg','../logohorizontal.png','../logovertical.png'].map(p=>new URL(p,self.registration.scope).href);
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await c.addAll(urls.map(p=>new Request(p,{cache:'reload'})));await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('sho-pwa-shell-')&&k!==CACHE)await caches.delete(k);await self.clients.claim()})()));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==self.location.origin)return;u.search='';if(!urls.includes(u.href))return;e.respondWith((async()=>{const c=await caches.open(CACHE);try{const r=await fetch(new Request(e.request,{cache:'no-cache'}));if(r.ok){await c.put(u.href,r.clone());return r}}catch(_){}return await c.match(u.href)||new Response('Abre a aplicação com internet uma primeira vez.',{status:503,headers:{'Content-Type':'text/plain;charset=utf-8'}})})())});
