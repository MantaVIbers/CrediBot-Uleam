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
