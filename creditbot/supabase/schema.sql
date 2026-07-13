-- Esquema de base de datos para CrediBot (PostgreSQL / Supabase)

-- Habilita la extensión para generar UUIDs
create extension if not exists "uuid-ossp";

-- Tabla de usuarios
create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    phone text not null unique,              -- Número de teléfono (único)
    full_name text,                          -- Nombre completo del usuario
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Tabla de conversaciones
create table if not exists conversations (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    current_state text not null default 'START',  -- Estado actual del flujo
    is_active boolean not null default true,       -- Indica si la conversación está activa
    last_message text,                             -- Último mensaje enviado
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Tabla de mensajes (historial)
create table if not exists messages (
    id uuid primary key default uuid_generate_v4(),
    conversation_id uuid not null references conversations(id) on delete cascade,
    user_id uuid not null references users(id) on delete cascade,
    direction text not null check (direction in ('inbound', 'outbound')),  -- 'inbound': del usuario, 'outbound': del bot
    content text not null,
    raw_payload jsonb,                         -- Payload original de Twilio (opcional)
    created_at timestamptz not null default now()
);

-- Tabla de solicitudes de crédito
create table if not exists credit_requests (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    conversation_id uuid not null references conversations(id) on delete cascade,
    requested_amount numeric(12, 2),           -- Monto solicitado
    term_months integer,                       -- Plazo en meses
    monthly_income numeric(12, 2),             -- Ingreso mensual
    estimated_payment numeric(12, 2),          -- Cuota estimada calculada
    payment_capacity numeric(12, 2),           -- Capacidad de pago calculada
    result text check (result in ('preaprobado', 'observado', 'no_cumple')),  -- Resultado de la evaluación
    status text not null default 'draft',      -- Estado: draft, completed
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Tabla de casos derivados a asesor humano
create table if not exists handoff_cases (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    conversation_id uuid not null references conversations(id) on delete cascade,
    credit_request_id uuid references credit_requests(id) on delete set null,  -- Solicitud relacionada (opcional)
    reason text not null,                       -- Motivo de la derivación
    status text not null default 'pending' check (status in ('pending', 'assigned', 'closed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- =====================================================================
-- CrediBot v2 — IA + tools + RAG (sección 10.2 del documento de arquitectura)
-- =====================================================================

-- Consentimiento e identidad del usuario (RF-08). La cédula se almacena en users
-- solo tras el consentimiento; los datos crediticios viven en credit_profiles.
alter table users add column if not exists cedula varchar(10) unique;
alter table users add column if not exists consent_given boolean not null default false;
alter table users add column if not exists consent_at timestamptz;

-- Perfil crediticio simulado (escala Ecuador 1–999). En producción vendría de un
-- buró (Equifax); aquí son datos FICTICIOS para fines académicos (política del curso).
create table if not exists credit_profiles (
    id uuid primary key default uuid_generate_v4(),
    cedula varchar(10) not null unique,
    full_name text not null,
    credit_score integer not null check (credit_score between 1 and 999),
    score_category text not null check (
        score_category in ('excelente', 'aceptable', 'regular', 'alto_riesgo')
    ),
    active_credits integer not null default 0,       -- Créditos vigentes
    total_debt numeric(12, 2) not null default 0,    -- Deuda total actual
    monthly_installments numeric(12, 2) not null default 0,  -- Cuotas mensuales vigentes
    has_delinquency boolean not null default false,  -- ¿Tiene mora activa?
    delinquency_days integer not null default 0,     -- Días de mora
    blacklisted boolean not null default false,      -- Lista negra
    thin_file boolean not null default false,        -- Sin historial suficiente
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists credit_profiles_cedula_idx on credit_profiles (cedula);

-- Historial de eventos crediticios asociados a un perfil (para trazabilidad/RAG).
create table if not exists credit_history_events (
    id uuid primary key default uuid_generate_v4(),
    credit_profile_id uuid not null references credit_profiles(id) on delete cascade,
    event_type text not null,   -- 'pago_puntual', 'mora', 'credito_nuevo', 'cancelacion'
    description text,
    event_date date,
    created_at timestamptz not null default now()
);

-- Auditoría de cada tool invocada por el agente GPT (RNF-04). La cédula se debe
-- enmascarar antes de guardar en los payloads.
create table if not exists tool_audit_logs (
    id uuid primary key default uuid_generate_v4(),
    conversation_id uuid references conversations(id) on delete set null,
    tool_name text not null,
    input_payload jsonb,
    output_payload jsonb,
    success boolean not null default true,
    latency_ms integer,
    created_at timestamptz not null default now()
);

create index if not exists tool_audit_logs_conversation_idx
    on tool_audit_logs (conversation_id);

-- Campos adicionales de la solicitud para el flujo v2 (score, categoría, monto máximo).
alter table credit_requests add column if not exists cedula varchar(10);
alter table credit_requests add column if not exists credit_score integer;
alter table credit_requests add column if not exists score_category text;
alter table credit_requests add column if not exists max_amount numeric(12, 2);
alter table credit_requests add column if not exists annual_rate numeric(5, 4);  -- TEA aplicada

-- =====================================================================
-- RAG — documentos de política de crédito indexados con pgvector (RF-07)
-- =====================================================================

-- Extensión de vectores para búsqueda semántica.
create extension if not exists vector;

create table if not exists rag_documents (
    id uuid primary key default uuid_generate_v4(),
    title text not null,
    source_path text,
    created_at timestamptz not null default now()
);

-- Chunks con embeddings. Dimensión 1536 = modelo text-embedding-3-small.
create table if not exists rag_chunks (
    id uuid primary key default uuid_generate_v4(),
    document_id uuid not null references rag_documents(id) on delete cascade,
    content text not null,
    embedding vector(1536),
    metadata jsonb,
    created_at timestamptz not null default now()
);

-- Índice para búsqueda por similitud coseno (opcional, mejora el rendimiento).
create index if not exists rag_chunks_embedding_idx
    on rag_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
