# LiqueDT system architecture

## Product boundary

LiqueDT is an XAUUSD context companion. It explains when liquidity is active and surfaces cross-market, calendar, and news context. It deliberately has no order entry, brokerage connection, position sizing, trade journaling, profit prediction, or autonomous alerts.

## System map

```text
Browser / installed PWA
  ├─ deterministic clock engine (Singapore, London, New York)
  ├─ session + OTC market state
  ├─ TradingView chart/ticker embeds
  ├─ calendar and headline views
  └─ experimental headline narrative UI
                 │ same-origin JSON
                 ▼
LiqueDT gateway (server.py in the MVP)
  ├─ request timeout and payload limits
  ├─ short in-memory cache + stale-if-error
  ├─ provider normalization
  ├─ XAUUSD relevance filter
  └─ bounded, explainable headline lexicon
       │                         │
       ▼                         ▼
Economic-calendar feed       Financial-news RSS
```

## Production target

The MVP is intentionally dependency-light, but each boundary maps cleanly to a production service:

| Layer | MVP | Scale-up path |
| --- | --- | --- |
| Web client | Static HTML/CSS/JS PWA | CDN-hosted versioned assets; React/Next only if interaction complexity earns it |
| API gateway | Python standard-library server | Stateless edge functions or containers behind a load balancer |
| Windows shell | .NET 6 `LiqueDT.exe` with an equivalent native gateway | Signed MSIX/installer with automated updates |
| Cache | Per-process memory | Redis with provider-specific TTL and stale-if-error windows |
| Market chart | TradingView public embed | Licensed WebSocket quote feed + first-party chart if commercial requirements demand it |
| Calendar | Normalized public feed | Licensed calendar provider adapter |
| News | FXStreet RSS adapter | Licensed real-time news provider adapter |
| Narrative | Transparent headline lexicon | Versioned NLP service with evaluation set, audit trail, confidence and human review |
| Observability | Health endpoint and process logs | OpenTelemetry traces, provider latency/error SLOs, freshness alerts and synthetic checks |

## API contracts

- `GET /api/health`: service availability and UTC server time.
- `GET /api/news`: relevant, normalized headlines plus an aggregate narrative object.
- `GET /api/calendar`: upcoming medium/high-impact USD events normalized to UTC; the client displays Singapore time.

Every feed response exposes `ok`, `source`, `updated_at`, and `stale`. The client refuses to show a narrative tilt when news cannot be verified.

## Reliability and data integrity

- Upstream requests have an eight-second timeout and a 2 MB response limit.
- News caches for three minutes; calendar data caches for fifteen minutes.
- A successful previous response is served as explicitly labelled cached data when an upstream refresh fails.
- Provider markup is stripped and all visible values are escaped before insertion into the DOM.
- Calendar timestamps are normalized to UTC on the gateway and rendered in `Asia/Singapore` by the client.
- Regional market sessions use IANA time zones, so London and New York daylight saving changes do not require hard-coded Singapore schedules.
- The market-open header is explicitly “indicative OTC hours”; broker holidays and maintenance can differ.

## Security

- The gateway binds to loopback by default.
- Content Security Policy restricts scripts and frames to LiqueDT and TradingView, fonts to Google Fonts, and connections to the same-origin API/TradingView.
- Camera, microphone, and geolocation are disabled by policy.
- External links open with `rel="noreferrer"`.
- No account credentials, brokerage data, cookies, or personal data are collected.

## Next production milestones

1. Obtain commercial redistribution rights and replace public-feed adapters with licensed providers.
2. Add persistent distributed caching and provider freshness monitoring.
3. Add an event taxonomy and historical evaluation suite for the narrative model before increasing its prominence.
4. Add contract tests for provider payload changes and end-to-end checks across desktop/mobile breakpoints.
5. Deploy the PWA to a CDN and the stateless gateway to two regions, with Singapore preferred routing.
