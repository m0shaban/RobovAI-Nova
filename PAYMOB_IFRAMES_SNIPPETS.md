# Paymob iFrames — Snippets جاهزة (Copy/Paste)

> الهدف: تحط أكواد بسيطة “حقيقية” في حقول **Html Content** و **Javascript Content** و **CSS Content** داخل Paymob iFrames.
>
> ملاحظة: Paymob أحيانًا بيقبل أي محتوى بسيط (حتى لو مش بيظهر للعميل). المهم يكون **غير فاضي** لو لوحة التحكم بتعتبره Required.

---

## 1) Html Content (انسخ كما هو)

> Paste في حقل **Html Content**

```html
<div id="robovai-paymob-brand" style="display:none">
  <span data-app="robovai-nova" data-purpose="paymob-iframe">RobovAI Nova</span>
</div>
```

- هذا HTML “حقيقي” و غير ضار، ومخفي (`display:none`) عشان ما يأثرش على واجهة Paymob.

---

## 2) Javascript Content (انسخ كما هو)

> Paste في حقل **Javascript Content**

```javascript
(function () {
  try {
    // Minimal safe script: tag the page + no side-effects
    document.documentElement.setAttribute('data-robovai', 'paymob-iframe');

    // Optional: basic console marker for debugging
    // console.log('RobovAI Paymob iframe loaded');
  } catch (e) {
    // Intentionally ignore
  }
})();
```

---

## 3) CSS Content (انسخ كما هو)

> Paste في حقل **CSS Content**

```css
/* Minimal safe CSS (no visual changes intended) */
:root {
  --robovai-paymob: 1;
}
#robovai-paymob-brand {
  display: none;
}
```

---

## 4) خطوات سريعة داخل Paymob

1. Developers → iFrames → Add
2. **Name**: أي اسم (مثلاً: `robovai`)
3. الصق الأكواد الثلاثة في الحقول
4. Save
5. خُد رقم الـ iFrame ID الناتج

### iFrame IDs الموجودة عندك (من الصورة)

- `442398` = **My new card iframe** (ده الأنسب للكارد في الغالب)
- `442397` = **Installment_Discount** (لو انت مفعّل Installments/Discounts وعايز نفس التجربة)

---

## 5) تربط iFrame ID في المشروع

في ملف `.env`:

```dotenv
PAYMOB_IFRAME_ID=442398
PAYMOB_INTEGRATION_ID=YOUR_CARD_INTEGRATION_ID
PAYMOB_API_KEY=YOUR_API_KEY
PAYMOB_HMAC_SECRET=YOUR_HMAC_SECRET
# PAYMOB_WALLET_INTEGRATION_ID=YOUR_WALLET_INTEGRATION_ID  # اختياري
```

> بعد تعديل `.env` لازم تعمل Restart للسيرفر.
