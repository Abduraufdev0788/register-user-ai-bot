import datetime
from typing import Any

# ANSI ranglari (ranglar terminalda chiroyli ko'rinishi uchun)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_bot_banner(name: str, username: str, phone: str = "") -> None:
    """Userbot muvaffaqiyatli ishga tushganda chiroyli banner chiqaradi."""
    border = "═" * 60
    print(f"\n{CYAN}{border}{RESET}")
    print(f"{GREEN}{BOLD}    👤 TELETHON USERBOT (SHAXSIY AKKAUNT) ISHGA TUSHDI!{RESET}")
    print(f"{CYAN}{border}{RESET}")
    print(f"{WHITE}  • Hisob egasi : {BOLD}{name}{RESET}")
    print(f"{WHITE}  • Username    : {CYAN}@{username}{RESET}")
    if phone:
        print(f"{WHITE}  • Telefon     : {WHITE}{phone}{RESET}")
    print(f"{WHITE}  • Kuzatuv     : {MAGENTA}Faqat shaxsiy (lichka) xabarlar{RESET}")
    print(f"{WHITE}  • Holat       : {GREEN}Faol (Yangi xabarlar kutilmoqda...){RESET}")
    print(f"{CYAN}{border}{RESET}\n")


def print_user_message(sender: Any = None, message_text: str = "", message_id: int = 0, date: datetime.datetime | None = None, chat_title: str | None = None) -> None:
    """
    Foydalanuvchi yuborgan xabar va uning ma'lumotlarini
    konsolga (terminalga) toza, chiroyli va tartibli shaklda chiqaradi.
    """
    sender_id = getattr(sender, "id", "Noma'lum")
    first_name = getattr(sender, "first_name", "") or ""
    last_name = getattr(sender, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip() or "Nomsiz"
    username = f"@{sender.username}" if getattr(sender, "username", None) else "Yo'q"
    is_premium = "Ha ⭐" if getattr(sender, "premium", False) else "Yo'q"
    phone = getattr(sender, "phone", None) or "Mavjud emas"
    if date:
        try:
            local_date = date.astimezone()
            time_str = local_date.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time_str = date.strftime("%Y-%m-%d %H:%M:%S")
    else:
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    box_width = 62
    divider = "─" * box_width

    print(f"\n{BLUE}┌{divider}┐{RESET}")
    print(f"{BLUE}│{RESET} {YELLOW}{BOLD}📩 YANGI FOYDALANUVCHI XABARI KELDI{RESET}{' ' * (box_width - 35)}{BLUE}│{RESET}")
    print(f"{BLUE}├{divider}┤{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}👤 Ism-familiya:{RESET} {WHITE}{full_name:<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}🆔 Telegram ID :{RESET} {CYAN}{str(sender_id):<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}🌐 Username    :{RESET} {MAGENTA}{username:<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}⭐ Premium     :{RESET} {WHITE}{is_premium:<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}📱 Telefon     :{RESET} {WHITE}{phone:<44}{RESET}{BLUE}│{RESET}")
    if chat_title:
        print(f"{BLUE}│{RESET} {BOLD}💬 Guruh/Kanal :{RESET} {WHITE}{chat_title[:44]:<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}⏰ Vaqt        :{RESET} {DIM}{time_str:<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}🔢 Xabar ID    :{RESET} {WHITE}{str(message_id):<44}{RESET}{BLUE}│{RESET}")
    print(f"{BLUE}├{divider}┤{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}💬 Xabar matni :{RESET}{' ' * (box_width - 16)}{BLUE}│{RESET}")

    import textwrap
    clean_text = (message_text or "<Matnsiz xabar / media>").strip()
    if not clean_text:
        clean_text = "<Bo'sh xabar>"

    for raw_line in clean_text.splitlines():
        wrapped = textwrap.wrap(raw_line, width=box_width - 4) or [""]
        for line in wrapped:
            print(f"{BLUE}│{RESET}   {GREEN}{line:<{box_width - 4}}{RESET} {BLUE}│{RESET}")

    print(f"{BLUE}└{divider}┘{RESET}\n")


def print_registration_success(user_data: dict, in_sheet: bool = False) -> None:
    """Foydalanuvchi to'liq ro'yxatdan o'tganda terminalda chiroyli yashil banner chiqaradi."""
    box_width = 62
    divider = "─" * box_width
    sheet_status = f"{GREEN}Yozildi ✅{RESET}" if in_sheet else f"{YELLOW}Mahalliy saqlandi (Sheets ulanmagan){RESET}"

    fn = user_data.get('first_name') or ''
    ln = user_data.get('last_name') or ''
    full_name = f"{fn} {ln}".strip() or "Noma'lum"
    phone = user_data.get("phone", "Kiritilmagan")
    birth_year = str(user_data.get("birth_year", "Kiritilmagan"))

    print(f"\n{GREEN}┌{divider}┐{RESET}")
    print(f"{GREEN}│{RESET} {GREEN}{BOLD}🎉 YANGI FOYDALANUVCHI RO'YXATDAN O'TDI!{RESET}{' ' * (box_width - 40)}{GREEN}│{RESET}")
    print(f"{GREEN}├{divider}┤{RESET}")
    print(f"{GREEN}│{RESET} {BOLD}👤 F.I.O        :{RESET} {WHITE}{full_name:<44}{RESET}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET} {BOLD}📱 Telefon      :{RESET} {WHITE}{phone:<44}{RESET}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET} {BOLD}🎂 Tug'ilgan yil:{RESET} {WHITE}{birth_year:<44}{RESET}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET} {BOLD}📊 Google Sheets:{RESET} {sheet_status:<53}{RESET}{GREEN}│{RESET}")
    print(f"{GREEN}└{divider}┘{RESET}\n")

