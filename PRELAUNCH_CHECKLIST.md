# Nova Pre-Launch Checklist

## 1) Security & Anti-abuse

- Rate limits applied for critical endpoints:
  - `POST /webhook` (chat)
  - `GET/POST /agent/stream` (chat streaming)
  - `GET /tools`, `GET /tools/list`
  - `POST /upload`, `POST /upload_image`, `POST /webhook_audio`
- Abuse guard middleware added with temporary block on repeated bursts.
- Request IDs + response-time headers added for tracing.

### Environment knobs

```bash
RL_CHAT_PER_MIN=60
RL_CHAT_STREAM_PER_MIN=45
RL_TOOLS_PER_MIN=120
RL_UPLOAD_PER_MIN=20
RL_AUDIO_PER_MIN=15
RL_ABUSE_BAN_SECONDS=120
SLOW_REQUEST_MS=1800
```

## 2) Monitoring (Errors + Latency + Alerts)

- Optional Sentry integration added.
- JSON metrics endpoint added: `GET /metrics/summary`
  - Protect with `METRICS_API_KEY` using header `x-api-key`.

### Sentry env

```bash
SENTRY_DSN=...
SENTRY_TRACES_SAMPLE_RATE=0.15
SENTRY_PROFILES_SAMPLE_RATE=0.0
RELEASE_VERSION=robovai-backend@v3
```

## 3) Legal Readiness

Pages added:

- `/privacy`
- `/terms`
- `/refund`

AI usage legal notice added in `chat.html` footer.

## 4) Smoke test before announce

Script:

```bash
python scripts/smoke_prelaunch.py
```

Required env vars:

```bash
SMOKE_BASE_URL=https://robovainova.onrender.com
SMOKE_EMAIL=...
SMOKE_PASSWORD=...
```

Checks covered:

- Health
- Login
- Chat via webhook
- Tools list
- Chatbot Builder page
- Smart Agents page
- Image generation command path
- Payment checkout initialization

## 5) Production payment full flow (manual final step)

Because card/wallet confirmation requires real user interaction (3DS / wallet confirmation), final validation is manual:

1. Login with real user account.
2. Open account/checkout and start `pro` subscription.
3. Complete provider confirmation screen (card/wallet).
4. Verify redirect to account success state.
5. Confirm webhook reached backend (`/payments/webhook/{provider}` logs).
6. Verify user tier/balance updated in DB and `/payments/subscription`.
7. Repeat for token package purchase.

> Keep webhook endpoint logs open during test to verify provider signatures/callbacks.
