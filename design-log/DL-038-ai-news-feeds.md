# DL-038 — AI news feeds in the default headline mix

## Background
User: "the news feeds also should contain AI news feeds." The
screensaver news widget defaults were BBC World + HN + Ars Technica —
general/tech only.

## Design
- Extend `rss.DEFAULT_FEEDS` with four verified, keyless AI feeds:
  The Verge AI (Atom), TechCrunch AI (RSS 2.0), OpenAI News (RSS 2.0),
  MIT Technology Review AI (RSS 2.0). Rejected candidates:
  Ars `/ai` (404), VentureBeat AI (429 to non-browser UAs).
- Parallel fetch (`ThreadPoolExecutor`, 8 workers) means 7 feeds cost
  the same latency as 3; a dead feed never blanks the widget.
- Settings help text updated to name the AI sources.

## Verification
- curl each feed → 200 + `<?xml` prolog confirmed.
- `fetch_headlines()` merge returns AI-source headlines.
- backend pytest + frontend vitest clean.
