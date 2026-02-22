"""Pre-launch smoke test for RobovAI Nova production readiness.

Covers:
- Auth (login)
- Core chat endpoint
- Tools listing
- Image generation command path
- Chatbot Builder / Smart Agents pages
- Payment checkout initialization

Usage (PowerShell):
  $env:SMOKE_BASE_URL="https://robovainova.onrender.com"
  $env:SMOKE_EMAIL="user@example.com"
  $env:SMOKE_PASSWORD="your-password"
  python scripts/smoke_prelaunch.py
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

import httpx


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


class SmokeTestError(Exception):
    """Raised when a critical smoke test step fails."""


async def _login(client: httpx.AsyncClient, email: str, password: str) -> CheckResult:
    response = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.status_code != 200:
        return CheckResult("login", False, f"status={response.status_code} body={response.text[:200]}")
    body = response.json()
    token = body.get("access_token")
    if not token:
        return CheckResult("login", False, "No access_token in response")
    client.headers["Authorization"] = f"Bearer {token}"
    return CheckResult("login", True, "Authenticated successfully")


async def _check_get(client: httpx.AsyncClient, path: str, name: str) -> CheckResult:
    response = await client.get(path)
    ok = response.status_code == 200
    return CheckResult(name, ok, f"status={response.status_code}")


async def _check_webhook_chat(client: httpx.AsyncClient) -> CheckResult:
    payload = {"user_id": "0", "message": "اكتب سطر ترحيب قصير", "platform": "web"}
    response = await client.post("/webhook", json=payload)
    if response.status_code != 200:
        return CheckResult("chat_webhook", False, f"status={response.status_code} body={response.text[:220]}")
    body = response.json()
    ok = body.get("status") in {"success", "ok"} and bool(body.get("response"))
    return CheckResult("chat_webhook", ok, f"status={body.get('status')} has_response={bool(body.get('response'))}")


async def _check_tools(client: httpx.AsyncClient) -> CheckResult:
    response = await client.get("/tools")
    if response.status_code != 200:
        return CheckResult("tools_list", False, f"status={response.status_code}")
    body = response.json()
    count = int(body.get("count", 0))
    return CheckResult("tools_list", count > 0, f"tools_count={count}")


async def _check_image_generation(client: httpx.AsyncClient) -> CheckResult:
    payload = {
        "message": "/generate_image futuristic cairo skyline at sunset",
        "user_id": "0",
        "platform": "web",
    }
    response = await client.post("/webhook", json=payload, timeout=120)
    if response.status_code != 200:
        return CheckResult("image_generation", False, f"status={response.status_code} body={response.text[:220]}")
    body = response.json()
    content = (body.get("response") or "").lower()
    ok = "http" in content or "![generated image]" in content
    return CheckResult("image_generation", ok, f"status={body.get('status')} content_preview={content[:80]}")


async def _check_checkout_init(client: httpx.AsyncClient) -> CheckResult:
    response = await client.post(
        "/payments/checkout",
        params={"plan": "pro", "provider": "auto", "method": "card"},
        timeout=60,
    )
    if response.status_code != 200:
        return CheckResult("payment_checkout_init", False, f"status={response.status_code} body={response.text[:220]}")
    body = response.json()
    checkout_url = body.get("checkout_url", "")
    ok = checkout_url.startswith("http")
    return CheckResult("payment_checkout_init", ok, f"provider={body.get('provider')} url_present={bool(checkout_url)}")


async def run_smoke() -> int:
    base_url = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    email = os.getenv("SMOKE_EMAIL", "").strip()
    password = os.getenv("SMOKE_PASSWORD", "").strip()

    if not email or not password:
        raise SmokeTestError("SMOKE_EMAIL and SMOKE_PASSWORD are required")

    timeout = httpx.Timeout(45.0, connect=15.0)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout, follow_redirects=True) as client:
        checks: list[CheckResult] = []

        checks.append(await _check_get(client, "/health", "health"))
        checks.append(await _login(client, email, password))

        if not checks[-1].ok:
            for item in checks:
                print(f"{'✅' if item.ok else '❌'} {item.name}: {item.detail}")
            return 1

        checks.append(await _check_webhook_chat(client))
        checks.append(await _check_tools(client))
        checks.append(await _check_get(client, "/chatbot-builder", "chatbot_builder_page"))
        checks.append(await _check_get(client, "/smart-agents", "smart_agents_page"))
        checks.append(await _check_image_generation(client))
        checks.append(await _check_checkout_init(client))

        failed = [c for c in checks if not c.ok]
        for item in checks:
            print(f"{'✅' if item.ok else '❌'} {item.name}: {item.detail}")

        if failed:
            print("\n⚠️ Smoke test finished with failures.")
            return 1

        print("\n🎉 Smoke test passed.")
        print("ℹ️ Final payment confirmation step (3DS/wallet confirmation) remains manual in production.")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_smoke()))
