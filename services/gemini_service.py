import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.1-flash-lite"


class GeminiService:
    """
    Google Gemini AI orqali foydalanuvchilar bilan suhbatlashish va
    ularning ma'lumotlarini (ism, familiya, telefon, tug'ilgan yil)
    suhbat davomida tabiiy ravishda yig'ish xizmati.
    """

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key
        # Agar model eskirgan 2.5 bo'lsa yoki bo'sh bo'lsa, 3.5-flash ga o'tamiz
        self.model_name = model_name if model_name and "2.5" not in model_name else DEFAULT_MODEL
        self.client = None
        self._conversations: Dict[int, List[dict]] = {}

        if self.api_key:
            self._init_client()
        else:
            logger.warning("GEMINI_API_KEY o'rnatilmagan. AI funksiyalari o'chirilgan.")

    def _init_client(self) -> None:
        """Google GenAI mijozini ishga tushirish."""
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Google GenAI mijozi muvaffaqiyatli ishga tushirildi (Model: {self.model_name}).")
        except Exception as e:
            logger.error(f"Gemini mijozini ishga tushirishda xatolik: {e}")

    def _extract_json_block(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        AI javobidagi ```json ... ``` blokini ajratib oladi va
        foydalanuvchiga ko'rinadigan matndan olib tashlaydi.
        """
        extracted_data = {}
        # json blokni qidirish
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        clean_text = text
        if match:
            json_str = match.group(1)
            try:
                extracted_data = json.loads(json_str)
                clean_text = re.sub(pattern, "", text, flags=re.DOTALL).strip()
            except Exception:
                pass
        else:
            inline_match = re.search(r"(\{[\"']first_name[\"'].*?\})", text, re.DOTALL)
            if inline_match:
                try:
                    extracted_data = json.loads(inline_match.group(1))
                    clean_text = text.replace(inline_match.group(1), "").strip()
                except Exception:
                    pass

        # Faqat bo'sh bo'lmagan haqiqiy qiymatlarni qoldiramiz
        valid_data = {}
        for k, v in extracted_data.items():
            if v is not None and v != "" and str(v).lower() not in ("null", "none"):
                valid_data[k] = v

        return clean_text.strip(), valid_data

    def _generate_fallback_response(
        self,
        user_message: str,
        current_data: Dict[str, Any],
        history: Optional[List[dict]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Agar API ishlamay qolsa (masalan 429 yoki 503 bo'lsa),
        FOYDALANUVCHIGA HECH QACHON ERROR KO'RSATILMAYDI.
        Buning o'rniga muloyim va insoniy qoidalar bo'yicha javob qaytariladi.
        Foydalanuvchi ma'lumotlarini o'zgartirishni ham to'liq qo'llab-quvvatlaydi.
        """
        extracted = {}
        msg_clean = user_message.strip()
        msg_lower = msg_clean.lower()

        NON_NAMES = {
            "salom", "assalomu", "alaykum", "start", "qalesan", "qalaysan", "qandaysiz",
            "qalaysiz", "yaxshimisiz", "charchamang", "tinchmi", "valaykum", "rahmat",
            "ok", "ha", "yoq", "yo'q", "bopti", "aloqa", "abuu", "abu", "privet",
            "hello", "hi", "qale", "qaleysan", "boladi", "tushundim", "hop", "xop",
            "ishlar", "qalay", "tuzukmisiz", "raxmat", "ozgartir", "o'zgartir",
            "ozgartirmoqchiman", "o'zgartirmoqchiman", "almashtir", "almashtirmoqchiman",
            "yangila", "yangilamoqchiman", "notogri", "noto'g'ri", "xato", "xatomi",
            "boshqa", "boshqacha", "kerak", "iltimos", "boladimi", "mumkinmi", "deb", "qoy", "qo'y"
        }

        # Oldingi xabarda bot nima so'raganini tekshiramiz
        last_bot_msg = ""
        if history and len(history) > 0:
            for item in reversed(history):
                if item.get("role") == "model":
                    last_bot_msg = item.get("text", "").lower()
                    break

        asked_for_first = "yangi ismingiz" in last_bot_msg or "ismingizni ayta olasizmi" in last_bot_msg or "ismingiz nima" in last_bot_msg
        asked_for_last = "yangi familiyangiz" in last_bot_msg or "familiyangizni ham" in last_bot_msg
        asked_for_phone = "yangi telefon" in last_bot_msg or "telefon raqamingizni" in last_bot_msg
        asked_for_year = "tug'ilgan yilingizni" in last_bot_msg

        # 1. FOYDALANUVCHI MA'LUMOTINI O'ZGARTIRMOQCHI BO'LGAN INTENTLARNI TEKSHIRAMIZ:
        # Agar "ismimni o'zgartirmoqchiman" deb yozsa va yangi ism berilmagan bo'lsa:
        if re.search(r"(?:ism|ismim|ismimni)\s*(?:o['`]?zgartir|almashtir|yangila)", msg_lower):
            explicit_name = re.search(r"(?:ismim|ismimni)\s+([A-Za-zА-Яа-яЎўҚқҒғҲҳ\']+)\s*(?:deb|ga|qilib)\s*o['`]?zgartir", msg_clean, re.IGNORECASE)
            if explicit_name and explicit_name.group(1).lower() not in NON_NAMES:
                extracted["first_name"] = explicit_name.group(1).capitalize()
                return f"Ismingiz {extracted['first_name']} ga muvaffaqiyatli o'zgartirildi ✅", extracted
            else:
                return "Albatta! Yangi ismingizni yozib yuboring, uni yangilab qo'yaman.", {}

        # Agar "familiyamni o'zgartirmoqchiman" desa:
        if re.search(r"(?:familiya|familiyam|familiyamni)\s*(?:o['`]?zgartir|almashtir|yangila)", msg_lower):
            explicit_last = re.search(r"(?:familiyam|familiyamni)\s+([A-Za-zА-Яа-яЎўҚқҒғҲҳ\']+)\s*(?:deb|ga|qilib)\s*o['`]?zgartir", msg_clean, re.IGNORECASE)
            if explicit_last and explicit_last.group(1).lower() not in NON_NAMES:
                extracted["last_name"] = explicit_last.group(1).capitalize()
                return f"Familiyangiz {extracted['last_name']} ga muvaffaqiyatli o'zgartirildi ✅", extracted
            else:
                return "Albatta! Yangi familiyangizni yozib yuboring.", {}

        # Agar "telefonimni o'zgartirmoqchiman" desa:
        if re.search(r"(?:telefon|telefonim|telefonimni|nomer|nomerim|nomerimni)\s*(?:o['`]?zgartir|almashtir|yangila)", msg_lower):
            phone_match = re.search(r"(\+?998\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}|\b\d{9}\b)", msg_clean)
            if not phone_match:
                return "Albatta! Yangi telefon raqamingizni yozib yuboring (masalan: +998901234567).", {}

        # Agar "yilimni o'zgartirmoqchiman" desa:
        if re.search(r"(?:yil|yilim|yilimni|tug['`]?ilgan)\s*(?:o['`]?zgartir|almashtir|yangila)", msg_lower):
            year_match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", msg_clean)
            if not year_match:
                return "Albatta! Tug'ilgan yilingizni yozib yuboring (masalan: 2004).", {}

        # 2. Regex orqali telefon raqamni aniqlash
        phone_match = re.search(r"(\+?998\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}|\b\d{9}\b)", msg_clean)
        if phone_match:
            raw_phone = re.sub(r"\s+", "", phone_match.group(1))
            if not raw_phone.startswith("+") and len(raw_phone) == 9:
                raw_phone = "+998" + raw_phone
            elif not raw_phone.startswith("+") and raw_phone.startswith("998"):
                raw_phone = "+" + raw_phone
            extracted["phone"] = raw_phone

        # 3. Regex orqali tug'ilgan yilni aniqlash (1950 - 2022)
        year_match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", msg_clean)
        if year_match:
            extracted["birth_year"] = int(year_match.group(1))

        # 4. Aniq ism/familiya shablonlari ("ismim Ali", "yangi ismim Ali", "mening ismim Ali")
        fn_match = re.search(r"(?:ismim|mening ismim|yangi ismim)\s+([A-Za-zА-Яа-яЎўҚқҒғҲҳ\']+)", msg_clean, re.IGNORECASE)
        if fn_match and fn_match.group(1).lower() not in NON_NAMES:
            extracted["first_name"] = fn_match.group(1).capitalize()

        ln_match = re.search(r"(?:familiyam|familiyamni|yangi familiyam)\s+([A-Za-zА-Яа-яЎўҚқҒғҲҳ\']+)", msg_clean, re.IGNORECASE)
        if ln_match and ln_match.group(1).lower() not in NON_NAMES:
            extracted["last_name"] = ln_match.group(1).capitalize()

        # 5. Agar bot oldingi xabarda ism so'ragan bo'lsa yoki 1-2 ta so'z kelsa:
        words = [w for w in msg_clean.split() if w.isalpha()]
        if asked_for_first and words:
            if words[0].lower() not in NON_NAMES:
                extracted["first_name"] = words[0].capitalize()
                if len(words) >= 2 and words[1].lower() not in NON_NAMES:
                    extracted["last_name"] = words[1].capitalize()
        elif asked_for_last and words:
            if words[0].lower() not in NON_NAMES:
                extracted["last_name"] = words[0].capitalize()
        # Hozirgi holatni yangilaymiz
        merged = {**current_data, **extracted}
        first_name = merged.get("first_name")
        last_name = merged.get("last_name")
        phone = merged.get("phone")
        birth_year = merged.get("birth_year")

        # Agar foydalanuvchi biror ma'lumotni o'zgartirgan bo'lsa
        if extracted and current_data.get("is_completed"):
            changed_items = []
            if "first_name" in extracted: changed_items.append(f"ismingiz ({extracted['first_name']})")
            if "last_name" in extracted: changed_items.append(f"familiyangiz ({extracted['last_name']})")
            if "phone" in extracted: changed_items.append(f"telefoningiz ({extracted['phone']})")
            if "birth_year" in extracted: changed_items.append(f"tug'ilgan yilingiz ({extracted['birth_year']})")
            return f"Qabul qilindi! {', '.join(changed_items)} muvaffaqiyatli yangilandi va saqlandi ✅", extracted

        # Ma'lumotlarni ketma-ket so'rash
        if not first_name:
            if any(w in msg_lower for w in ("salom", "assalomu", "qalesan", "qalaysan", "privet")):
                reply = "Salom! Yaxshimisiz? Ro'yxatdan o'tasizmi?"
            elif any(w in msg_lower for w in ("ha", "otaman", "o'taman", "mayli", "albatta")):
                reply = "Ajoyib! Ismingiz nima?"
            else:
                reply = "Siz ham ro'yxatdan o'tasizmi? Ismingiz nima?"
        elif not last_name:
            reply = f"Rahmat, {first_name}! Familiyangiz nima?"
        elif not phone:
            reply = "Telefon raqamingizni yozib yuborsangiz (+998...)"
        elif not birth_year:
            reply = "Tug'ilgan yilingiz nechanchi yil?"
        else:
            reply = f"Rahmat, {first_name}! Ma'lumotlaringiz saqlandi ✅"

        return reply, extracted

    async def get_response(
        self,
        user_id: int,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Foydalanuvchi bilan tabiiy muloqot qiladi va ro'yxatdan o'tish
        ma'lumotlarini (ism, familiya, telefon, tug'ilgan yil) ajratib oladi.
        Hech qachon xatolik qaytarmaydi (Safe Fallback).
        """
        current_data = user_profile or {}

        # Agar API kalit umuman yo'q bo'lsa yoki mijoz ishlamasa, darhol fallback
        history = self._conversations.setdefault(user_id, [])
        if not self.api_key or not self.client:
            return self._generate_fallback_response(user_message, current_data, history)

        known_status = (
            f"Foydalanuvchi ma'lumotlari holati:\n"
            f"- Ismi: {current_data.get('first_name') or 'noma\'lum'}\n"
            f"- Familiyasi: {current_data.get('last_name') or 'noma\'lum'}\n"
            f"- Telefon raqami: {current_data.get('phone') or 'noma\'lum'}\n"
            f"- Tug'ilgan yili: {current_data.get('birth_year') or 'noma\'lum'}\n"
        )

        system_instruction = (
            "Siz Telegramda foydalanuvchilarni ro'yxatga oluvchi jonli, samimiy va xushmuomala insondek suhbatlashuvchi yordamchisiz.\n\n"
            "ASOSIY USLUB VA QOIDALAR:\n"
            "1. ODAMGA O'XSHAB QISQA JAVOB BERING:\n"
            "   - Hech qachon uzun, rasmiy yoki robotdek gapirmang! Javoblaringiz 1-2 ta qisqa gapdan oshmasin.\n"
            "   - Telegramda oddiy insonlar qanday yozishsa, shunday do'stona va tabiiy javob bering.\n"
            "   - Salomlashsa: alik olib, 'Yaxshimisiz? Ro'yxatdan o'tasizmi?' deb so'rang.\n"
            "   - Savol bersa yoki umumiy gap yozsa: savoliga qisqa (1 gap) javob berib, 'Siz ham ro'yxatdan o'tasizmi?' deb taklif qiling.\n\n"
            "2. MA'LUMOTLARNI BOSQICHMA-BOSQICH YIG'ISH:\n"
            "   Foydalanuvchi 'Ha', 'o'taman', 'albatta' desa yoki ro'yxatdan o'tishga rozi bo'lsa, undan 4 ta ma'lumotni navbatma-navbat va juda qisqa so'rang:\n"
            "   1) first_name — 'Ajoyib! Ismingiz nima?'\n"
            "   2) last_name — 'Rahmat! Familiyangiz nima?'\n"
            "   3) phone — 'Telefon raqamingizni yozib yuborsangiz (+998...)'\n"
            "   4) birth_year — 'Tug'ilgan yilingiz nechanchi yil?'\n"
            "   (Agar foydalanuvchi birdaniga bir nechta ma'lumot yozsa, ularni oling va yetishmayotganini so'rang).\n\n"
            "3. ISM VA GAPLARNI AJRATISH (O'TA MUHIM):\n"
            "   - Umumiy gaplar, savollar va fe'llar (masalan: 'salom', 'ha', 'barcha', 'tadbirda', 'buyruqlarni', 'qalesan') HECH QACHON ism emas!\n"
            "   - Faqat foydalanuvchi aniq o'z ismini aytgandagina (masalan: 'Abdurauf', 'Ismim Ali') first_name deb oling.\n\n"
            "4. MA'LUMOTLARNI O'ZGARTIRISH:\n"
            "   - Agar foydalanuvchi 'ismimni o'zgartirmoqchiman' desa, yangi ismini so'rang.\n"
            "   - Yangi qiymat aytilsa, uni yangilang.\n\n"
            "5. NATIJANI JSON FORMATDA QAYTARISH:\n"
            "   - Aniqlangan yoki yangilangan ma'lumotlarni FAQAT javobingiz oxirida ```json ... ``` blokida bering:\n"
            "```json\n"
            "{\"first_name\": \"...\"}\n"
            "```\n"
            "   - Agar yangi ma'lumot bo'lmasa (masalan 'salom', 'ha', oddiy savol), JSON BLOKNI UMUMAN QO'SHMANG!\n"
            "   - Hamma ma'lumot to'plangach: 'Rahmat! Ma'lumotlaringiz saqlandi ✅' deb qisqa tasdiqlang."
        )

        prompt_parts = []
        for turn in history[-6:]:
            prompt_parts.append(f"{turn['role']}: {turn['text']}")
        prompt_parts.append(f"user: {user_message}\n\n[Hozirgi ma'lumotlar: {known_status}]")
        full_prompt = "\n".join(prompt_parts)

        # Ishchi va mavjud modellarni zaxira sifatida sinash
        candidate_models = [
            self.model_name,
            "gemini-3.1-flash-lite",
            "gemini-flash-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
        ]
        unique_models = []
        for m in candidate_models:
            if m and m not in unique_models:
                unique_models.append(m)

        response = None
        for current_model in unique_models:
            for attempt in range(2):
                try:
                    response = await self.client.aio.models.generate_content(
                        model=current_model,
                        contents=full_prompt,
                        config={
                            "system_instruction": system_instruction,
                            "temperature": 0.5,
                        }
                    )
                    if response and response.text:
                        break
                except Exception as err:
                    err_str = str(err)
                    logger.warning(f"Model '{current_model}' so'rovida xatolik ({err_str[:60]}), navbatdagisiga urinilmoqda...")
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        await asyncio.sleep(0.5)
                    else:
                        break
            if response and response.text:
                break

        # Agar barcha modellar ishlamasa (masalan 429 limit tugasa), xavfsiz fallback beramiz
        if not response or not response.text:
            logger.warning("Barcha Gemini modellari javob bermadi, xavfsiz fallback javobi ishlatilmoqda.")
            fallback_text, extracted_fallback = self._generate_fallback_response(user_message, current_data, history)
            history.append({"role": "user", "text": user_message})
            history.append({"role": "model", "text": fallback_text})
            return fallback_text, extracted_fallback

        raw_text = response.text
        clean_text, extracted_data = self._extract_json_block(raw_text)

        # Tarixga toza matnni qo'shamiz
        history.append({"role": "user", "text": user_message})
        history.append({"role": "model", "text": clean_text})

        return clean_text, extracted_data
