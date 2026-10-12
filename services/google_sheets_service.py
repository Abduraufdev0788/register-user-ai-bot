import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
import urllib.request
import json

logger = logging.getLogger(__name__)


class GoogleSheetService:
    """
    Foydalanuvchi ma'lumotlarini Google Sheets jadvaliga avtomatik yozuvchi xizmat.
    Google Apps Script Webhook yoki gspread orqali ishlaydi.
    """

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url.strip()
        self._locks: Dict[str, asyncio.Lock] = {}
        if self.webhook_url:
            logger.info("Google Sheets Webhook xizmati faollashtirildi.")
        else:
            logger.info("GOOGLE_SHEETS_WEBHOOK_URL ko'rsatilmagan (Google Sheets integratsiyasi kutish rejimida).")

    def _get_user_lock(self, user_id: str) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def add_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Foydalanuvchi ma'lumotlarini Google Sheets ga async rejimda qo'shish.
        Parallel so'rovlar dublikat yaratmasligi uchun user bo'yicha lock ishlatiladi.
        """
        if not self.webhook_url:
            logger.debug("Google Sheets Webhook URL kiritilmagan, jadvalga yozish o'tkazib yuborildi.")
            return False

        user_id_str = str(user_data.get("user_id", ""))
        user_lock = self._get_user_lock(user_id_str)

        async with user_lock:
            payload = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user_id_str,
                "username": user_data.get("username", "") or "",
                "tg_first_name": user_data.get("tg_first_name", "") or "",
                "first_name": user_data.get("first_name", "") or "",
                "last_name": user_data.get("last_name", "") or "",
                "phone": user_data.get("phone", "") or "",
                "birth_year": str(user_data.get("birth_year", "") or ""),
                "is_completed": bool(user_data.get("is_completed", False)),
                "created_at": user_data.get("created_at", "") or "",
                "updated_at": user_data.get("updated_at", "") or "",
            }

            loop = asyncio.get_running_loop()
            try:
                success = await loop.run_in_executor(None, self._send_request, payload)
                if success:
                    display_name = f"{payload['first_name']} {payload['last_name']}".strip() or payload.get('tg_first_name') or payload['user_id']
                    logger.info(f"📊 Google Sheets ga yozildi/yangilandi: {display_name} (ID: {payload['user_id']})")
                return success
            except Exception as e:
                logger.error(f"Google Sheets ga yozishda xatolik: {e}")
                return False


    def _send_request(self, payload: dict) -> bool:
        """Sinxron HTTP POST so'rovi (executor orqali chaqiriladi)."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                return response.status in (200, 201, 302)
        except Exception as e:
            logger.warning(f"Google Sheets so'rovi muvaffaqiyatsiz: {e}")
            return False
