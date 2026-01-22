-- Ensure betting platform policies are idempotent

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'value_bets' AND policyname = 'Allow read access to value_bets'
  ) THEN
    CREATE POLICY "Allow read access to value_bets" ON public.value_bets FOR SELECT USING (true);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'game_context' AND policyname = 'Allow read access to game_context'
  ) THEN
    CREATE POLICY "Allow read access to game_context" ON public.game_context FOR SELECT USING (true);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'injury_impact' AND policyname = 'Allow read access to injury_impact'
  ) THEN
    CREATE POLICY "Allow read access to injury_impact" ON public.injury_impact FOR SELECT USING (true);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'line_movements' AND policyname = 'Allow read access to line_movements'
  ) THEN
    CREATE POLICY "Allow read access to line_movements" ON public.line_movements FOR SELECT USING (true);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'bet_history' AND policyname = 'Users can view own bet history'
  ) THEN
    CREATE POLICY "Users can view own bet history" ON public.bet_history FOR SELECT USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'bet_history' AND policyname = 'Users can insert own bets'
  ) THEN
    CREATE POLICY "Users can insert own bets" ON public.bet_history FOR INSERT WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'bet_history' AND policyname = 'Users can update own bets'
  ) THEN
    CREATE POLICY "Users can update own bets" ON public.bet_history FOR UPDATE USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_bankroll' AND policyname = 'Users can view own bankroll'
  ) THEN
    CREATE POLICY "Users can view own bankroll" ON public.user_bankroll FOR SELECT USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_bankroll' AND policyname = 'Users can update own bankroll'
  ) THEN
    CREATE POLICY "Users can update own bankroll" ON public.user_bankroll FOR UPDATE USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_bankroll' AND policyname = 'Users can insert own bankroll'
  ) THEN
    CREATE POLICY "Users can insert own bankroll" ON public.user_bankroll FOR INSERT WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'active_exposure' AND policyname = 'Users can view own exposure'
  ) THEN
    CREATE POLICY "Users can view own exposure" ON public.active_exposure FOR SELECT USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'active_exposure' AND policyname = 'Users can insert own exposure'
  ) THEN
    CREATE POLICY "Users can insert own exposure" ON public.active_exposure FOR INSERT WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'active_exposure' AND policyname = 'Users can update own exposure'
  ) THEN
    CREATE POLICY "Users can update own exposure" ON public.active_exposure FOR UPDATE USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_alerts' AND policyname = 'Users can view own alerts'
  ) THEN
    CREATE POLICY "Users can view own alerts" ON public.user_alerts FOR SELECT USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_alerts' AND policyname = 'Users can update own alerts'
  ) THEN
    CREATE POLICY "Users can update own alerts" ON public.user_alerts FOR UPDATE USING (user_id = auth.uid());
  END IF;
END $$;
