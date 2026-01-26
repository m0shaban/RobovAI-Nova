# 🚨 حل مشكلة الـ Webhook

## المشكلة

- ❌ الـ Webhook غير مضبوط على Telegram
- ⏳ هناك 3 رسائل معلقة لم تصل للبوت
- البوت لا يستقبل أي رسائل

## الحل السريع ⚡

### الطريقة 1: باستخدام Script (الأسهل)

```bash
python scripts/setup_webhook.py
```

ثم الصق الـ Render URL عندما يطلب منك.

---

### الطريقة 2: يدوياً (مضمونة 100%)

#### الخطوة 1: احصل على Render URL

1. اذهب إلى: <https://dashboard.render.com/web/srv-d5r2m9i4d50c738pbqf0>
2. انسخ الـ URL (مثل: `https://robovai-nova.onrender.com`)

#### الخطوة 2: اضبط الـ Webhook

عدّل الأمر التالي بوضع رابط Render الخاص بك:

```bash
curl -X POST "https://api.telegram.org/bot8278684938:AAFtchJWEjou-Y5BlasvDqDZgsv04g16p4Q/setWebhook" -H "Content-Type: application/json" -d "{\"url\":\"YOUR_RENDER_URL/telegram-webhook\"}"
```

**مثال**:

```bash
curl -X POST "https://api.telegram.org/bot8278684938:AAFtchJWEjou-Y5BlasvDqDZgsv04g16p4Q/setWebhook" -H "Content-Type: application/json" -d "{\"url\":\"https://robovai-nova.onrender.com/telegram-webhook\"}"
```

#### الخطوة 3: تحقق من النجاح

```bash
python scripts/diagnose_webhook.py
```

يجب أن ترى:

```
✅ Webhook URL looks correct
```

---

## ✅ النتيجة المتوقعة

بعد ضبط الـ Webhook:

1. ✅ الـ 3 رسائل المعلقة سترسل للبوت فوراً
2. ✅ البوت سيرد على جميع الرسائل الجديدة
3. ✅ اللوجات ستظهر في Render Dashboard

---

## 🔧 (اختياري) ضبط في Render Environment

لتجنب هذه المشكلة مستقبلاً:

1. اذهب إلى Render Dashboard > Environment
2. أضف:

   ```
   EXTERNAL_URL=https://your-app.onrender.com
   ```

3. Redeploy

بهذا، الـ webhook سيُضبط تلقائياً عند كل deployment.
