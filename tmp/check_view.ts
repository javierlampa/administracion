
import { createClient } from '@supabase/supabase-api-js';
import dotenv from 'dotenv';
dotenv.config({ path: 'portal/.env.local' });

async function checkView() {
    const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
    const { data, error } = await supabase.from('v_todas_las_op_report').select('*').limit(1);
    if (error) {
        console.error(error);
        return;
    }
    console.log("Columns:", Object.keys(data[0] || {}));
}

checkView();
