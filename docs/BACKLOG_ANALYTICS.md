# Backlog rozwoju (analityka + UX)

## Priorytety

### P0 — szybkie wygrane (1–3 dni)
- `Top 5` w analizie zespołów (filtrowanie po aktualnym sortowaniu).
  - Estymacja: S (0.5–1d)
  - Zależności: brak.
- Szybkie przełączniki okna formy `Last 5/10` w Form Tracker.
  - Estymacja: S (0.5d)
  - Zależności: brak.
- Badge’e `value / edge / confidence` z tooltipem i linkiem do metodologii.
  - Estymacja: S (1d)
  - Zależności: dokument metodologii w `docs/`.

### P1 — rozszerzenia analityki (3–7 dni)
- Filtry/sortowanie w analizach: konferencja, bilans, forma last 5/10, home/away.
  - Estymacja: M (3–4d)
  - Zależności: ujednolicenie pól w `/api/teams/analysis` (last5/10, home/away).
- Historia i porównania: trend formy, porównanie sezon vs last 10, mini‑sparklines.
  - Estymacja: M (3–5d)
  - Zależności: endpoint z danymi historycznymi lub agregacja frontowa.
- Alerty i powiadomienia: subskrypcje zespołów + line movement.
  - Estymacja: M (4–6d)
  - Zależności: tabela `subscriptions`, job backendowy, kanał notyfikacji.

### P2 — fundamenty produktu (1–2 tyg.)
- Onboarding i edukacja: mini‑tutorial + tooltipy metryk.
  - Estymacja: M (5–7d)
  - Zależności: słownik metryk i tłumaczenia.
- Wydajność: caching wyników analityki + lazy‑loading cięższych sekcji.
  - Estymacja: L (7–10d)
  - Zależności: decyzja o cache (Redis/in‑memory), invalidacja.
- Panel statusu danych: scraper/odświeżanie, ostatnia aktualizacja, błędy.
  - Estymacja: M/L (6–10d)
  - Zależności: endpoint `health/data` + monitoring jobów.

## Kolejność wdrożeń (propozycja)
1. Top 5 + Last 5/10 (P0) → poprawa czytelności danych.
2. Badge’e value/edge/confidence (P0) → kontekst decyzji.
3. Filtry home/away + last5/10 w analizie zespołów (P1) → głębsza eksploracja.
4. Historia + sparklines (P1) → szybkie trendy.
5. Alerty + subskrypcje (P1) → retencja.
6. Onboarding + panel statusu danych (P2) → jakość i zaufanie.
7. Cache + lazy‑loading (P2) → skala i koszt.
