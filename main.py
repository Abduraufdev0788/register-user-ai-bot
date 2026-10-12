import asyncio
import logging
import sys
from telethon import TelegramClient

from config import get_config
from handlers import register_handlers
from services import GeminiService, StorageService, GoogleSheetService
from utils import print_bot_banner

# Asosiy log sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot")


async def main() -> None:
    """Botni ishga tushirish va asosiy boshqaruv funksiyasi."""
    try:
        cfg = get_config()
    except Exception as exc:
        logger.error(f"Konfiguratsiya xatosi: {exc}")
        sys.exit(1)

    logger.info("Xizmatlar sozlanmoqda (Gemini AI, Storage, Google Sheets)...")
    gemini_service = GeminiService(
        api_key=cfg.gemini_api_key,
        model_name=cfg.gemini_model,
    )
    storage_service = StorageService()
    google_sheet_service = GoogleSheetService(cfg.google_sheets_webhook_url)

    logger.info("Telethon Telegram mijozi ishga tushirilmoqda...")
    client = TelegramClient(
        cfg.session_name,
        cfg.api_id,
        cfg.api_hash,
    )

    # User akkaunt (userbot) sifatida kirish
    if cfg.phone_number:
        logger.info(f"Foydalanuvchi akkauntiga ulanmoqda ({cfg.phone_number})...")
        await client.start(phone=cfg.phone_number)
    else:
        logger.info("Foydalanuvchi akkauntiga ulanmoqda...")
        await client.start()

    # Akkaunt ma'lumotlarini olish
    me = await client.get_me()
    first_name = getattr(me, "first_name", "") or ""
    last_name = getattr(me, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip() or "Telegram Foydalanuvchi"
    username = getattr(me, "username", "") or "Mavjud emas"
    phone = getattr(me, "phone", "") or ""

    print_bot_banner(
        name=full_name,
        username=username,
        phone=phone,
    )

    # Handlerlarni ro'yxatdan o'tkazamiz (shaxsiy xabarlar uchun)
    register_handlers(
        client=client,
        gemini_service=gemini_service,
        storage_service=storage_service,
        google_sheet_service=google_sheet_service,
        only_private=cfg.only_private,
    )

    # Mavjud to'liq ro'yxatdan o'tgan foydalanuvchilarni Google Sheets ga sinxronizatsiya qilish
    if cfg.google_sheets_webhook_url:
        for u_id, u_data in storage_service.get_all_users().items():
            if u_data.get("is_completed"):
                asyncio.create_task(google_sheet_service.add_user(u_data))

    # Foydalanuvchi akkauntini xabarlarni kutish rejimida ushlab turamiz
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi.")
