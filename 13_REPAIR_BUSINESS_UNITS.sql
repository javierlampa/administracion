-- 13. REPAIR BUSINESS UNITS
-- Script para auto-vincular unidades de negocio a las OPs existentes basándose en el campo 'empresa'.

INSERT INTO unidades_negocio (op_id, unidad_negocio)
SELECT op.id, 
    CASE 
        WHEN LOWER(op.empresa) LIKE '%canal telesol%' THEN 'Canal Telesol'
        WHEN LOWER(op.empresa) LIKE '%canal zonda%' THEN 'Canal Zonda'
        WHEN LOWER(op.empresa) LIKE '%canal 5%' THEN 'CANAL 5'
        WHEN LOWER(op.empresa) LIKE '%diario papel%' THEN 'Diario Papel'
        WHEN LOWER(op.empresa) LIKE '%digital el zonda%' THEN 'Digital El Zonda'
        WHEN LOWER(op.empresa) LIKE '%digital telesol%' THEN 'Digital Telesol'
        WHEN LOWER(op.empresa) LIKE '%imprenta%' THEN 'Imprenta'
        WHEN LOWER(op.empresa) LIKE '%radio am%' THEN 'RADIO AM'
        WHEN LOWER(op.empresa) LIKE '%radio 1020%' THEN 'Radio 1020'
        WHEN LOWER(op.empresa) LIKE '%redes sociales%' THEN 'Redes Sociales'
        ELSE 'TODOS'
    END
FROM ordenes_publicidad op
WHERE NOT EXISTS (SELECT 1 FROM unidades_negocio un WHERE un.op_id = op.id);

-- Opcional: Verificación
-- SELECT op.op, op.empresa, un.unidad_negocio 
-- FROM ordenes_publicidad op 
-- JOIN unidades_negocio un ON op.id = un.op_id 
-- LIMIT 20;
