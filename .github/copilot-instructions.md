# Copilot Instructions — AI Solutions & Development Company

## Company Context

You are assisting a **professional AI solutions & software development company** that builds:

- AI agents and chatbots (Python, Flask, LLMs, Telegram bots)
- Web applications (React, Next.js, TypeScript, Flask)
- Mobile applications (React Native / Expo)
- Backend APIs and services (Python FastAPI/Flask, Node.js)

---

## Core Coding Standards (NON-NEGOTIABLE)

### Universal Rules

- Always write **production-ready**, clean, and well-documented code
- Apply **SOLID principles** and **clean architecture**
- Every function/class must be **type-annotated**
- Add meaningful **docstrings** and inline comments where logic is non-obvious
- Handle **all edge cases and error scenarios** explicitly
- Never hardcode secrets, API keys, or passwords — always use **environment variables**

### Python / AI Agents

```python
# Always use:
from typing import Optional, List, Dict, Any
import logging
import asyncio

# Async-first for all I/O operations
async def process_data(input: str) -> Optional[Dict[str, Any]]:
    """
    Brief description of what this function does.

    Args:
        input: The input data to process

    Returns:
        Processed result or None if failed

    Raises:
        ValueError: If input is invalid
    """
```

- Use **strict type hints** on all functions and class attributes
- Use **async/await** for all I/O operations (API calls, DB queries, file I/O)
- Use **custom exception classes** that inherit from a base project exception
- Use **structured logging** (`logging.getLogger(__name__)`) never `print()`
- Use **Pydantic** for data validation in APIs
- Prefer **dataclasses** or **Pydantic models** over raw dicts
- Use **context managers** for resource management

### TypeScript / React Native

- **Strict mode** always (`"strict": true` in tsconfig)
- **Never use `any`** — use `unknown` or proper types instead
- Use **functional components** + React hooks exclusively
- Props must have **explicit interface definitions**
- Use **React Query / TanStack Query** for server state
- Use **Zustand or Context API** for client state (not Redux unless existing)
- All API calls go through a **typed service layer** (`/services/`)

### Flask / FastAPI Backend

- Always use **input validation** (Pydantic or marshmallow)
- Return proper **HTTP status codes** (never return 200 for errors)
- All endpoints must have **try/except** with proper error responses
- Use **JWT** for authentication, validate on every protected route
- Never expose database errors or stack traces to the client

---

## Project Architecture Patterns

### Python Project Structure

```
project/
├── app/
│   ├── api/          # Route handlers (thin, delegate to services)
│   ├── services/     # Business logic
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas (request/response)
│   ├── core/         # Config, security, exceptions
│   └── utils/        # Pure helper functions
├── tests/
├── .env.example
└── requirements.txt
```

### React Native / Web Project Structure

```
src/
├── components/       # Reusable UI components
├── screens/          # Screen-level components (RN) or pages/ (Next.js)
├── services/         # API calls (typed)
├── hooks/            # Custom React hooks
├── stores/           # Zustand stores
├── types/            # TypeScript type definitions
├── utils/            # Pure helper functions
└── config/           # App configuration
```

---

## AI/LLM Development Specific Rules

- Always add **rate limiting** to LLM API calls
- Implement **retry logic with exponential backoff** for external API calls
- Cache LLM responses when the same input can repeat (Redis preferred)
- Never log full user prompts — hash or truncate sensitive content
- Track **token usage** and enforce limits per user/session
- Use **streaming responses** for conversational UI when possible

---

## Commit Message Format

```
type(scope): short description (max 72 chars)

Types: feat | fix | refactor | docs | style | test | chore | perf
Example: feat(auth): add JWT refresh token rotation
```

---

## What to AVOID

- ❌ `any` type in TypeScript
- ❌ `print()` for logging in Python (use `logging`)
- ❌ Hardcoded credentials or magic strings
- ❌ Synchronous blocking calls in async functions
- ❌ Missing error handling in API routes
- ❌ Direct database queries in route handlers
- ❌ Returning 200 status on errors
- ❌ Storing sensitive data in frontend state or localStorage
