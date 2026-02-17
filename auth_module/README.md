# 🔐 RobovAI Auth Module — Standalone Package

نظام تسجيل + تسجيل دخول + تفعيل عبر Telegram OTP — جاهز للنقل لأي تطبيق FastAPI.

## الملفات

| ملف                | الوظيفة                                                |
| ------------------- | ----------------------------------------------------- |
| `security.py`       | JWT tokens, password hashing, password validation      |
| `database.py`       | SQLite: users, sessions, OTP, CRUD                     |
| `auth_routes.py`    | FastAPI routes: signup, login, logout, OTP, verify, me  |
| `telegram_verify.py`| Telegram bot: inline buttons, email/phone verification |
| `config.py`         | Settings / environment variables                       |
| `models.py`         | Pydantic request/response models                       |

## الاستخدام السريع

```python
# main.py
from fastapi import FastAPI
from auth_module.auth_routes import auth_router
from auth_module.telegram_verify import create_telegram_app

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Telegram webhook
telegram_app = create_telegram_app()
```

## المتطلبات

```
fastapi>=0.100.0
pyjwt>=2.8.0
passlib[bcrypt]>=1.7.4
pydantic-settings>=2.0.0
python-telegram-bot>=22.0
python-dotenv>=1.0.0
python-multipart>=0.0.6
```

## البيئة (.env)

```env
JWT_SECRET_KEY=your-secret-key-min-32-chars
TELEGRAM_BOT_TOKEN=your-bot-token
DATABASE_PATH=users.db
EXTERNAL_URL=https://your-app.com
```
