import os
from dataclasses import dataclass
from dotenv import load_dotenv

# .env faylini yuklaymiz
load_dotenv()


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    bot_token: str = ""
    phone_number: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    session_name: str = "user_session"
    only_private: bool = True
    google_sheets_webhook_url: str = ""

    @classmethod
    def load(cls) -> "Config":
        raw_api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH", "").strip()
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        phone_number = os.getenv("PHONE_NUMBER", "").strip()
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
        session_name = os.getenv("SESSION_NAME", "user_session").strip()
        only_private_val = os.getenv("ONLY_PRIVATE", "true").lower() in ("true", "1", "yes")
        google_sheets_webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL", "").strip()

        errors = []
        if not raw_api_id:
            errors.append("API_ID (.env faylida ko'rsatilmagan)")
        if not api_hash:
            errors.append("API_HASH (.env faylida ko'rsatilmagan)")

        if errors:
            raise ValueError(
                "Quyidagi muhim parametrlar yetishmayapti:\n - " + "\n - ".join(errors) +
                "\nIltimos, .env faylini to'ldiring (.env.example ga qarang)."
            )

        try:
            api_id = int(raw_api_id)
        except ValueError:
            raise ValueError(f"API_ID raqam bo'lishi kerak, berilgan qiymat: {raw_api_id}")

        return cls(
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            phone_number=phone_number,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            session_name=session_name,
            only_private=only_private_val,
            google_sheets_webhook_url=google_sheets_webhook_url,
        )


_cached_config: Config | None = None


def get_config() -> Config:
    global _cached_config
    if _cached_config is None:
        _cached_config = Config.load()
    return _cached_config

