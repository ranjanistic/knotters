const assets = [

  "/static/styles/w3.css"
  
]


self.addEventListener('install', event => {
  console.log('Service worker installed!!');
  
  event.waitUntil(
    caches.open('cache')
      .then(cache => {
        console.log('caching in  process');
        cache.addAll(assets);
    })
  )
  });
  
  self.addEventListener('activate', event => {
    console.log('Service worker activated!!');
  });




