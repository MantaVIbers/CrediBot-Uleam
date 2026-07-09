create extension if not exists "uuid-ossp";

create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    phone text not null unique,
    full_name text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists conversations (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    current_state text not null default 'START',
    is_active boolean not null default true,
    last_message text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists messages (
    id uuid primary key default uuid_generate_v4(),
    conversation_id uuid not null references conversations(id) on delete cascade,
    user_id uuid not null references users(id) on delete cascade,
    direction text not null check (direction in ('inbound', 'outbound')),
    content text not null,
    raw_payload jsonb,
    created_at timestamptz not null default now()
);

create table if not exists credit_requests (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    conversation_id uuid not null references conversations(id) on delete cascade,
    requested_amount numeric(12, 2),
    term_months integer,
    monthly_income numeric(12, 2),
    estimated_payment numeric(12, 2),
    payment_capacity numeric(12, 2),
    result text check (result in ('preaprobado', 'observado', 'no_cumple')),
    status text not null default 'draft',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists handoff_cases (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    conversation_id uuid not null references conversations(id) on delete cascade,
    credit_request_id uuid references credit_requests(id) on delete set null,
    reason text not null,
    status text not null default 'pending' check (status in ('pending', 'assigned', 'closed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
