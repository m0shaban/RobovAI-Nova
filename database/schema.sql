-- RobovAI Supabase Schema
-- Enable UUID extension
create extension if not exists "uuid-ossp";
-- USERS TABLE
create table public.profiles (
    id uuid references auth.users not null primary key,
    full_name text,
    telegram_id text unique,
    whatsapp_id text unique,
    token_balance integer default 10,
    is_premium boolean default false,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);
-- Enable RLS
alter table public.profiles enable row level security;
-- TRANSACTIONS TABLE (for top-ups)
create table public.transactions (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references public.profiles(id) not null,
    amount_paid numeric(10, 2) not null,
    tokens_added integer not null,
    payment_method text not null,
    -- 'fawry', 'instapay', 'vodafone_cash'
    status text default 'pending',
    -- 'pending', 'completed', 'failed'
    transaction_ref text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
-- TOOL USAGE LOGS (Analytics)
create table public.tool_usage (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references public.profiles(id) not null,
    tool_name text not null,
    -- '/social', '/imagine', etc.
    tokens_consumed integer not null,
    input_summary text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
-- PROMPT TEMPLATES (Management)
create table public.prompt_templates (
    id uuid default uuid_generate_v4() primary key,
    tool_name text not null unique,
    template_text text not null,
    description text,
    is_active boolean default true,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
-- CHATBOT BUILDER TABLES
create table public.user_chatbots (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references public.profiles(id) not null,
    name text not null,
    description text,
    bot_type text default 'hybrid',
    -- 'ai_only', 'rules_only', 'hybrid'
    system_prompt text,
    temperature numeric(3, 2) default 0.7,
    -- probability/creativity control
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
create table public.chatbot_integrations (
    id uuid default uuid_generate_v4() primary key,
    bot_id uuid references public.user_chatbots(id) not null,
    platform text not null,
    -- 'telegram', 'web', 'whatsapp', 'facebook'
    access_token text,
    webhook_url text,
    is_active boolean default true
);
create table public.crm_contacts (
    id uuid default uuid_generate_v4() primary key,
    bot_id uuid references public.user_chatbots(id) not null,
    platform_user_id text not null,
    name text,
    phone text,
    interactions_count integer default 0,
    last_interaction timestamp with time zone default timezone('utc'::text, now())
);
-- CONTENT ORBIT (SMART AGENT) TABLES
create table public.content_campaigns (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references public.profiles(id) not null,
    name text not null,
    ai_persona text not null,
    is_active boolean default true,
    schedule_cron text default '0 * * * *' -- Hourly default
);
create table public.content_sources (
    id uuid default uuid_generate_v4() primary key,
    campaign_id uuid references public.content_campaigns(id) not null,
    source_type text not null,
    -- 'rss', 'api'
    source_url text not null
);
create table public.agent_publishing_logs (
    id uuid default uuid_generate_v4() primary key,
    campaign_id uuid references public.content_campaigns(id) not null,
    user_id uuid references public.profiles(id) not null,
    content text not null,
    original_link text,
    status text default 'published',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
-- FUNCTIONS & TRIGGERS
-- Function to handle new user signup (auto-create profile)
create or replace function public.handle_new_user() returns trigger as $$ begin
insert into public.profiles (id, full_name, token_balance)
values (new.id, new.raw_user_meta_data->>'full_name', 10);
return new;
end;
$$ language plpgsql security definer;
-- Trigger for new auth.users
-- drop trigger if exists on_auth_user_created on auth.users;
-- create trigger on_auth_user_created
--   after insert on auth.users
--   for each row execute procedure public.handle_new_user();
-- Function to deduct tokens
create or replace function public.deduct_tokens(p_user_id uuid, p_amount integer) returns boolean as $$
declare current_bal integer;
begin
select token_balance into current_bal
from public.profiles
where id = p_user_id;
if current_bal >= p_amount then
update public.profiles
set token_balance = token_balance - p_amount,
    updated_at = now()
where id = p_user_id;
return true;
else return false;
end if;
end;
$$ language plpgsql security definer;