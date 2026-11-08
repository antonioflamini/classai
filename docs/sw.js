const C="classai-v3";
self.addEventListener("install",()=>self.skipWaiting());
self.addEventListener("fetch",e=>{if(new URL(e.request.url).origin!==location.origin)return;
 e.respondWith(fetch(e.request).then(r=>{const k=r.clone();caches.open(C).then(c=>c.put(e.request,k));return r}).catch(()=>caches.match(e.request)))});
