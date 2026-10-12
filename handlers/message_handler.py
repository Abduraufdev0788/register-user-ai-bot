import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import User

from services.gemini_service import GeminiService
from services.storage_service import StorageService
from services.google_sheets_service import GoogleSheetService
from utils.printer import print_user_message, print_registration_success

logger = logging.getLogger(__name__)


def register_handlers(
    client: TelegramClient,
    gemini_service: GeminiService,
    storage_service: StorageService,
    google_sheet_service: GoogleSheetService,
    only_private: bool = True,
) -> None:
    """Barcha xabar hodisalarini (event handlers) ro'yxatdan o'tkazadi."""

    @client.on(events.NewMessage)
    async def on_new_message(event: events.NewMessage.Event) -> None:
        try:
            # 1. O'zimiz yuborgan (outgoing) xabarlarni o'tkazib yuboramiz
            if event.out:
                return

            # 2. Agar faqat shaxsiy (lichka) xabarlar belgilangan bo'lsa, guruh/kanallarni o'tkazib yuboramiz
            if only_private and not event.is_private:
                return

            sender = await event.get_sender()
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", None)

            sender_id = getattr(sender, "id", None) or event.sender_id

            # 3. Telegram rasmiy xabarlari (777000 - kirish kodlari) yoki o'zimiz bo'lsa javob bermaymiz
            if sender_id == 777000 or getattr(sender, "is_self", False):
                return

            # 4. Boshqa botlardan kelgan xabarlarga javob qaytarmaymiz
            if getattr(sender, "bot", False):
                return

            message_text = event.raw_text or ""
            message_id = event.id
            date = event.date

            # 5. Foydalanuvchi ma'lumotlarini konsolga/terminalga chiroyli qilib print qilamiz
            print_user_message(
                sender=sender if isinstance(sender, User) else None,
                message_text=message_text,
                message_id=message_id,
                date=date,
                chat_title=chat_title,
            )

            # Maxsus /clear yoki /reset buyrug'i (kesh va tarixni tozalash)
            if message_text.strip().lower() in ("/clear", "/reset", "tozalash"):
                if sender_id in gemini_service._conversations:
                    gemini_service._conversations[sender_id].clear()
                storage_service.reset_user(sender_id)
                await event.reply("🧹 Suhbat tarixingiz va ro'yxatdan o'tish ma'lumotlaringiz tozalandi. Qaytadan boshlashingiz mumkin!")
                return

            # Agar matnsiz media bo'lsa
            if not message_text.strip():
                await event.reply("Kechirasiz, hozircha faqat matnli xabarlar orqali ro'yxatdan o'tishingiz mumkin.")
                return

            # 6. Foydalanuvchini bazadan olish yoki yangisini yaratish
            tg_first_name = getattr(sender, "first_name", "") or ""
            tg_username = getattr(sender, "username", "") or ""
            user_data = storage_service.init_user_if_not_exists(
                user_id=sender_id,
                tg_first_name=tg_first_name,
                username=tg_username,
            )
            was_completed_before = user_data.get("is_completed", False)

            # 7. Telegramda 'yozmoqda...' (typing) statusini ko'rsatish
            async with event.client.action(event.chat_id, "typing"):
                reply_text, extracted_fields = await gemini_service.get_response(
                    user_id=sender_id,
                    user_message=message_text,
                    user_profile=user_data,
                )

            # 8. Agar suhbatdan yangi ma'lumotlar ajratib olingan bo'lsa, bazaga saqlaymiz
            updated_user = storage_service.update_user(sender_id, **extracted_fields) if extracted_fields else user_data

            # 8. Faqatgina ro'yxatdan to'liq o'tganda (yoki ma'lumotlarini o'zgartirganda) Google Sheets ga yuboramiz.
            # Bu har bitta oraliq xabarda takroriy 4 marta jadvalga yozilishining oldini oladi!
            should_sync = False
            if updated_user.get("is_completed"):
                if not was_completed_before:
                    should_sync = True
                    print_registration_success(
                        user_data=updated_user,
                        in_sheet=bool(google_sheet_service.webhook_url),
                    )
                elif extracted_fields:
                    # Allaqachon ro'yxatdan o'tgan foydalanuvchi biror ma'lumotini o'zgartirdi
                    should_sync = True
                    logger.info(f"Foydalanuvchi {sender_id} ma'lumotlarini yangiladi: {extracted_fields}")

            if should_sync:
                async def _sync_sheet(u):
                    success = await google_sheet_service.add_user(u)
                    if success:
                        storage_service.mark_sheet_synced(sender_id)

                asyncio.create_task(_sync_sheet(updated_user))

            # 9. Foydalanuvchiga toza va muloyim javob qaytarish
            await event.reply(reply_text)

        except Exception as error:
            # FOYDALANUVCHIGA HECH QACHON ERRORNI KO'RSATMAYMIZ!
            logger.error(f"Xabarni qayta ishlashda xatolik: {error}", exc_info=True)
            try:
                await event.reply("Assalomu alaykum! Xabaringiz qabul qilindi. Siz bilan tez orada bog'lanamiz!")
            except Exception:
                pass
