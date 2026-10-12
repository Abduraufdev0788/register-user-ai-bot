"""
Loyiha kirish nuqtasi (alias).
Asosiy mantiq main.py da joylashgan.
"""
import asyncio
from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi.")
