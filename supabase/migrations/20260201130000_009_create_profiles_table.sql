-- Create profiles table linked to Supabase auth users.
-- Stores app-specific user data.

create table if not exists public.profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  email text,
  role text default 'user',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_profiles_email on public.profiles (email);

alter table public.profiles enable row level security;

-- Allow users to read their own profile; service role can read all.
create policy "profiles_select_own"
  on public.profiles
  for select
  using (auth.uid() = user_id or auth.role() = 'service_role');

-- Allow users to update their own profile; service role can update all.
create policy "profiles_update_own"
  on public.profiles
  for update
  using (auth.uid() = user_id or auth.role() = 'service_role')
  with check (auth.uid() = user_id or auth.role() = 'service_role');

-- Allow service role to insert (users are created via trigger).
create policy "profiles_insert_service"
  on public.profiles
  for insert
  with check (auth.role() = 'service_role' or auth.uid() = user_id);

-- Keep updated_at current.
create or replace function public.set_profile_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_profiles_updated_at on public.profiles;
create trigger set_profiles_updated_at
before update on public.profiles
for each row execute function public.set_profile_updated_at();

-- Auto-create profile on signup.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (user_id, email, role)
  values (new.id, new.email, 'user')
  on conflict (user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- Backfill profiles for existing auth users.
insert into public.profiles (user_id, email, role)
select u.id, u.email, 'user'
from auth.users u
left join public.profiles p on p.user_id = u.id
where p.user_id is null;
