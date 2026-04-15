fetch('https://ehodsnqdspswuzzdsgoe.supabase.co/rest/v1/', { 
    headers: { 'apikey': 'sb_publishable_v6ZXCSnWIACt6XflH5JTpQ_8ik3q682' } 
})
.then(r => r.json())
.then(j => {
    console.log("--- CATALOGO DE TABLAS/VISTAS ---");
    console.log(Object.keys(j.definitions || {}).sort().join('\n'));
})
.catch(err => console.error(err));
