# 🤖 Telethon & Gemini AI Telegram Userbot (Foydalanuvchilarni Ro'yxatga Olish)

Ushbu bot shaxsiy Telegram akkauntingizga (lichkangizga) kelgan foydalanuvchilar bilan **tabiiy va muloyim suhbat qurgan holda** ularning ma'lumotlarini to'playdi, mahalliy bazaga va avtomatik ravishda **Google Sheets** jadvaliga yozadi.

---

### 🌟 Asosiy Imkoniyatlar

1. **Tabiiy Suhbat Orqali Ro'yxatdan O'tkazish:**
   - Foydalanuvchidan quyidagi ma'lumotlarni bosqichma-bosqich, muloyimlik bilan so'rab oladi:
     - 👤 **Ismi**
     - 👥 **Familiyasi**
     - 📱 **Telefon raqami**
     - 🎂 **Tug'ilgan yili**
2. **Nol Xatolik (Zero Error Exposure):**
   - Hatto Google Gemini API vaqtincha ishlamay qolsa (masalan, kvota yoki server tirbandligi bo'lsa), foydalanuvchiga HECH QACHON texnik xatolik (error, traceback) ko'rinmaydi. Tizim avtomatik ravishda insoniy va do'stona qoidalar orqali suhbatni uzluksiz davom ettiradi.
3. **📊 Google Sheets Integratsiyasi:**
   - Foydalanuvchi ma'lumotlari to'liq to'plangach, ma'lumotlar avtomatik tarzda Google Sheets jadvaliga yangi qator bo'lib yoziladi.
4. **💾 Mahalliy zaxira:**
   - Barcha ma'lumotlar `data/users.json` faylida ham xavfsiz saqlanib boriladi.
5. **🖥️ Chiroyli Terminal Print:**
   - Har bir xabar va ro'yxatdan o'tgan foydalanuvchi terminalda rangli va tartibli ramkada ko'rinadi.

---

## 📁 Loyiha Strukturasi (Clean Architecture)

```
register-user-ai-bot/
├── config/                  # Sozlamalar (.env yuklash va tekshirish)
├── handlers/                # Telegram xabarlarini qayta ishlash
├── services/
│   ├── gemini_service.py    # AI muloqoti va ma'lumotlarni ajratish
│   ├── storage_service.py   # Foydalanuvchilarni JSON bazada saqlash
│   └── google_sheets_service.py # Google Sheets ga avtomatik yozish
├── utils/                   # Terminalga chiroyli print chiqarish
├── data/                    # users.json saqlanadigan papka
├── google_sheets_script.js  # Google Sheets Apps Script kodi
├── main.py                  # Asosiy kirish nuqtasi
└── .env                     # API kalitlar va sozlamalar
```

---

## 📊 Google Sheets Integratsiyasini Sozlash (1 daqiqada)

Google Cloud yoki murakkab to'lovli hisoblar shart emas! Quyidagi 4 qadamni bajaring:

1. [sheets.new](https://sheets.new) orqali yangi Google Sheets jadvalini oching.
2. Yuqori menyudan: **Kengaytmalar (Extensions)** ➡️ **Apps Script** ni bosing.
3. Oynadagi kodni o'chirib, loyihamizdagi [`google_sheets_script.js`](file:///home/abdurauf/dasturlash/git_hub/register-user-ai-bot/google_sheets_script.js) ichidagi kodni nusxalab joylashtiring.
4. Yuqoridagi **Deploy (Joylashtirish)** ➡️ **New deployment (Yangi joylashtirish)** ni bosing:
   - Chap tarafdagi tishli g'ildirakchadan **Web app** ni tanlang.
   - **Who has access (Kim kira oladi):** `Anyone` (Har kim) ni tanlang.
   - **Deploy** tugmasini bosing va berilgan **Web app URL** dan nusxa oling.
5. Olingan URL manzilini `.env` faylidagi `GOOGLE_SHEETS_WEBHOOK_URL` ga qo'ying:
   ```ini
   GOOGLE_SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/AKfycbx.../exec
   ```

---

## 🚀 Ishga Tushirish

```bash
python main.py
```
