-- Remove duplicates and enforce uniqueness for player_game_stats

-- 1) Delete duplicates, keep the smallest id per (game_id, player_id)
DELETE FROM player_game_stats a
USING player_game_stats b
WHERE a.id > b.id
  AND a.game_id = b.game_id
  AND a.player_id = b.player_id;

-- 2) Add unique index to prevent future duplicates
CREATE UNIQUE INDEX IF NOT EXISTS uq_player_game_stats_game_player
ON player_game_stats (game_id, player_id);
