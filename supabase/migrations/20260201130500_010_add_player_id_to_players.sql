-- Add missing player_id column to players and index it.

alter table public.players
  add column if not exists player_id bigint;

create index if not exists idx_players_player_id
  on public.players (player_id);
