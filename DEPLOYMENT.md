# RobovAI Nova - Deploy to Render 🚀

## خطوات النشر على Render (الأسهل والأفضل)

### 1️⃣ تجهيز المشروع

```bash
# إنشاء GitHub Repository
git init
git add .
git commit -m "RobovAI Nova - Ready for deployment"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2️⃣ إنشاء حساب على Render

- اذهب إلى [render.com](https://render.com)
- سجل دخول باستخدام GitHub

### 3️⃣ إنشاء Web Service

1. اضغط **"New +"** → **"Web Service"**
2. اختر الـ Repository الخاص بك
3. **الإعدادات:**
   - **Name**: `robovai-nova`
   - **Region**: `Frankfurt` (الأقرب للشرق الأوسط)
   - **Branch**: `main`
   - **Root Directory**: اتركه فارغ
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### 4️⃣ Environment Variables (مهم جداً!)

في صفحة الإعدادات، أضف المتغيرات التالية:

```
GROQ_API_KEY=gsk_your_key_here
NVIDIA_API_KEY=nvapi-your_key_here
IMGBB_API_KEY=your_imgbb_key_here
EXTERNAL_URL=https://robovai-nova.onrender.com (رابط مشروعك بعد الإنشاء)
TELEGRAM_BOT_TOKEN=your_bot_token
```

### 5️⃣ Deploy

- اضغط **"Create Web Service"**
- انتظر 2-3 دقائق للنشر

### 6️⃣ الرابط النهائي

```
https://robovai-nova.onrender.com
```

---

## ⚠️ ملاحظات مهمة

### الخطة المجانية

- ✅ 750 ساعة/شهر مجاناً
- ⚠️ السيرفر ينام بعد 15 دقيقة من عدم الاستخدام
- 🔄 يستيقظ تلقائياً عند أول طلب (30 ثانية)

### قاعدة البيانات

- SQLite تعمل لكن البيانات تُحذف عند إعادة النشر
- للإنتاج: استخدم PostgreSQL من Render (مجاني أيضاً)

---

## 🎯 البدائل الأخرى

### Railway.app

```bash
# تثبيت Railway CLI
npm i -g @railway/cli

# تسجيل الدخول
railway login

# النشر
railway up
```

### Fly.io

```bash
# تثبيت Fly CLI
curl -L https://fly.io/install.sh | sh

# تسجيل الدخول
fly auth login

# النشر
fly launch
fly deploy
```

---

## ✅ الملفات المطلوبة (تم إنشاؤها)

- [`Procfile`](file:///f:/New%20folder%20%2824%29/Procfile) - أمر تشغيل السيرفر
- [`requirements.txt`](file:///f:/New%20folder%20%2824%29/requirements.txt) - المكتبات المطلوبة
- [`.gitignore`](file:///f:/New%20folder%20%2824%29/.gitignore) - ملفات يتم تجاهلها

---

## 🧪 اختبار بعد النشر

```bash
# Health Check
curl https://robovai-nova.onrender.com/health

# الصفحة الرئيسية
https://robovai-nova.onrender.com/

# الشات
https://robovai-nova.onrender.com/chat
```

🎉 **البوت الآن أونلاين 24/7!**
