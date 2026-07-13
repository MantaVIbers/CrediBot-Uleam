-- =====================================================================
-- Seed de perfiles crediticios FICTICIOS para CrediBot v2
-- =====================================================================
-- Política del curso: NO usar datos reales. Todas las cédulas son ficticias
-- pero válidas según el algoritmo módulo 10 de Ecuador, para que pasen la tool
-- `validar_cedula`. Los nombres, scores y deudas son inventados.
--
-- Cobertura: las 4 categorías (excelente / aceptable / regular / alto_riesgo)
-- más casos de mora activa y lista negra, para demostrar todas las rutas del bot.
--
-- Ejecutar en el SQL Editor de Supabase DESPUÉS de schema.sql.
-- Idempotente: se puede correr varias veces sin duplicar (ON CONFLICT).
-- =====================================================================

insert into credit_profiles (
    cedula, full_name, credit_score, score_category,
    active_credits, total_debt, monthly_installments,
    has_delinquency, delinquency_days, blacklisted, thin_file
) values
    -- Excelentes (750–999)
    ('0911111110', 'Carlos Ortiz Vera',        820, 'excelente',   0,     0.00,   0.00, false,  0, false, false),
    ('0922222229', 'Ana Lucía Vera Palma',     900, 'excelente',   2,  5000.00, 180.00, false,  0, false, false),
    ('0101010106', 'Pedro Salas Ochoa',        780, 'excelente',   1,  2000.00, 120.00, false,  0, false, false),
    ('1305050500', 'Andrés Loor Zambrano',     760, 'excelente',   0,     0.00,   0.00, false,  0, false, false),
    ('0909090904', 'Fernando Palma Rivas',     850, 'excelente',   1,  1000.00,  90.00, false,  0, false, false),
    ('0303030308', 'Hugo Macías Delgado',      750, 'excelente',   1,  1200.00, 100.00, false,  0, false, false),

    -- Aceptables (550–749)
    ('0912345675', 'María González López',     720, 'aceptable',   1,  3200.00, 150.00, false,  0, false, false),
    ('0933333338', 'Luis Mero Andrade',        650, 'aceptable',   1,  1500.00, 110.00, false,  0, false, false),
    ('1710034560', 'Sofía Andrade Cuenca',     600, 'aceptable',   2,  3500.00, 200.00, false,  0, false, false),
    ('1313131318', 'Gabriela Cuenca Ríos',     700, 'aceptable',   1,  2500.00, 130.00, false,  0, false, false),
    ('1340040045', 'Karla Intriago Solórzano', 580, 'aceptable',   1,  1800.00, 105.00, false,  0, false, false),
    ('0102030400', 'Daniela Ponce Bravo',      620, 'aceptable',   0,     0.00,   0.00, false,  0, false, true),
    ('0505050500', 'Paola Cortez Mendoza',     550, 'aceptable',   1,  2200.00, 125.00, false,  0, false, false),

    -- Regulares (349–549)
    ('0944444447', 'Jorge Cedeño Loor',        420, 'regular',     3,  8000.00, 320.00, false,  0, false, false),
    ('1712345675', 'Diego Ramírez Vélez',      500, 'regular',     2,  6000.00, 280.00, false,  0, false, false),
    ('1707070700', 'Valeria Suárez Chávez',    350, 'regular',     1,  4000.00, 210.00, false,  0, false, false),
    ('0818181810', 'Lucía Vélez Moreira',      470, 'regular',     2,  5500.00, 260.00, false,  0, false, false),

    -- Alto riesgo (< 349)
    ('0955555552', 'Elena Bravo Muñoz',        280, 'alto_riesgo', 4, 12000.00, 480.00, true,  90, false, false),
    ('1320020025', 'Marcos Zambrano Pico',     200, 'alto_riesgo', 5, 15000.00, 600.00, true, 120, true,  false),
    ('1800180018', 'Roberto Chávez Alcívar',   320, 'alto_riesgo', 3,  9000.00, 400.00, false,  0, false, false),

    -- Caso especial: score alto PERO con mora activa (la mora descalifica igual)
    ('0919191916', 'Tomás Freire Santos',      800, 'excelente',   2,  4000.00, 220.00, true,  60, false, false)
on conflict (cedula) do nothing;

-- Algunos eventos de historial de ejemplo (opcional, enriquece el panel y el RAG).
insert into credit_history_events (credit_profile_id, event_type, description, event_date)
select id, 'pago_puntual', 'Pago puntual de cuota de consumo', date '2026-05-10'
from credit_profiles where cedula = '0912345675'
on conflict do nothing;

insert into credit_history_events (credit_profile_id, event_type, description, event_date)
select id, 'mora', 'Atraso de 90 días en tarjeta de crédito', date '2026-03-15'
from credit_profiles where cedula = '0955555552'
on conflict do nothing;

insert into credit_history_events (credit_profile_id, event_type, description, event_date)
select id, 'credito_nuevo', 'Apertura de microcrédito', date '2026-01-20'
from credit_profiles where cedula = '0919191916'
on conflict do nothing;
