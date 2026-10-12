import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

STORAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")


class StorageService:
    """
    Foydalanuvchilar ma'lumotlarini (ism, familiya, telefon, tug'ilgan yil)
    xavfsiz saqlash va boshqarish xizmati.
    """

    def __init__(self, file_path: str = STORAGE_FILE):
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Fayl va papka mavjudligini ta'minlash."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4, ensure_ascii=False)

    def _load_all(self) -> Dict[str, Any]:
        """Barcha foydalanuvchilar ma'lumotini o'qish."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Foydalanuvchilar faylini o'qishda xatolik: {e}")
            return {}

    def _save_all(self, data: Dict[str, Any]) -> None:
        """Barcha ma'lumotlarni faylga yozish."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Foydalanuvchilarni saqlashda xatolik: {e}")

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Foydalanuvchini ID bo'yicha olish."""
        all_users = self._load_all()
        return all_users.get(str(user_id))

    def init_user_if_not_exists(self, user_id: int, tg_first_name: str = "", username: str = "") -> Dict[str, Any]:
        """Foydalanuvchini birinchi marta boshlang'ich holatda ro'yxatga kiritish."""
        all_users = self._load_all()
        uid = str(user_id)
        if uid not in all_users:
            all_users[uid] = {
                "user_id": user_id,
                "username": username or "",
                "tg_first_name": tg_first_name or "",
                "first_name": None,
                "last_name": None,
                "phone": None,
                "birth_year": None,
                "is_completed": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save_all(all_users)
        return all_users[uid]

    def update_user(self, user_id: int, **fields) -> Dict[str, Any]:
        """Foydalanuvchining ma'lumotlarini yangilash."""
        all_users = self._load_all()
        uid = str(user_id)
        user = all_users.setdefault(uid, {
            "user_id": user_id,
            "first_name": None,
            "last_name": None,
            "phone": None,
            "birth_year": None,
            "is_completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        for key, value in fields.items():
            if value is not None:
                user[key] = value

        # Agar barcha 4 ta maydon to'ldirilgan bo'lsa, ro'yxatdan o'tgan deb hisoblaymiz
        if user.get("first_name") and user.get("last_name") and user.get("phone") and user.get("birth_year"):
            user["is_completed"] = True

        user["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_all(all_users)
        return user

    def mark_sheet_synced(self, user_id: int) -> None:
        """Foydalanuvchi Google Sheets ga muvaffaqiyatli yozilganini belgilash."""
        all_users = self._load_all()
        uid = str(user_id)
        if uid in all_users:
            all_users[uid]["sheet_synced"] = True
            self._save_all(all_users)

    def reset_user(self, user_id: int) -> bool:
        """Foydalanuvchi ma'lumotlarini (kesh/bazadan) tozalash (qaytadan ro'yxatdan o'tishi uchun)."""
        all_users = self._load_all()
        uid = str(user_id)
        if uid in all_users:
            del all_users[uid]
            self._save_all(all_users)
            return True
        return False

    def get_all_users(self) -> Dict[str, Any]:
        """Barcha foydalanuvchilar lug'atini olish."""
        return self._load_all()
