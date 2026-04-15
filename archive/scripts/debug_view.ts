import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
    'https://ehodsnqdspswuzzdsgoe.supabase.co',
    'sb_publishable_v6ZXCSnWIACt6XflH5JTpQ_8ik3q682'
);

async function checkView() {
    console.log("--- DEBUG V_REPORTE_PROGRAMAS ---");
    const { data, error } = await supabase.from('v_reporte_programas').select('*').limit(1);
    
    if (error) {
        console.error("ERROR:", error.message);
    } else if (!data || data.length === 0) {
        console.log("LA VISTA ESTÁ VACÍA");
    } else {
        console.log("COLUMNAS:", Object.keys(data[0]));
        console.log("MUESTRA:", JSON.stringify(data[0], null, 2));
    }
}

checkView();
