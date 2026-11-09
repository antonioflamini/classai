const C="classai-v6";
self.addEventListener("install",()=>self.skipWaiting());
self.addEventListener("activate",e=>e.waitUntil(self.clients.claim()));
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);
 // "Condividi → ClassAI" (Android): il PDF arriva qui, lo metto da parte e apro l'app che lo legge
 if(e.request.method==="POST"&&u.origin===location.origin&&u.searchParams.has("share")){
  e.respondWith((async()=>{try{const fd=await e.request.formData(),f=fd.get("pdf");
   if(f&&f.size){const c=await caches.open("classai-share");await c.put("shared-file",new Response(f,{headers:{"Content-Type":f.type||"application/pdf","X-Name":encodeURIComponent(f.name||"circolare.pdf")}}))}}catch(err){}
   return Response.redirect(new URL("./?shared=1",self.registration.scope).href,303)})());return}
 if(e.request.method!=="GET"||u.origin!==location.origin)return;
 e.respondWith(fetch(e.request).then(r=>{const k=r.clone();caches.open(C).then(c=>c.put(e.request,k));return r}).catch(()=>caches.match(e.request)))});
