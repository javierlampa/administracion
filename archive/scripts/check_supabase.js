const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.resolve(__dirname, 'portal/.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkData() {
    console.log('Checking with Supabase-JS...');
    
    // Check total count
    const { count, error: countError } = await supabase
        .from('ordenes_publicidad')
        .select('*', { count: 'exact', head: true });
    
    if (countError) {
        console.error('Error fetching count:', countError);
    } else {
        console.log('Total OPs:', count);
    }

    // Check matches for today (2026-04-07)
    const targetDate = '2026-04-07';
    const { data: matches, error: matchError } = await supabase
        .from('ordenes_publicidad')
        .select('id, op, inicio_pauta, fin_pauta, activo')
        .lte('inicio_pauta', targetDate)
        .gte('fin_pauta', targetDate)
        .limit(5);

    if (matchError) {
        console.error('Error fetching matches:', matchError);
    } else {
        console.log(`Matches for ${targetDate}:`, matches?.length || 0);
        console.log('Sample matches:', matches);
    }

    // Check activo status
    const { data: activoCheck, error: activoError } = await supabase
        .from('ordenes_publicidad')
        .select('activo')
        .limit(10);
    
    if (activoError) {
        console.error('Error checking activo:', activoError);
    } else {
        console.log('Sample activo flags:', activoCheck.map(r => r.activo));
    }
}

checkData();
