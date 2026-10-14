import os
import httpx
from dotenv import load_dotenv
import asyncio

load_dotenv()


async def send_telegram_alert(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"

    if not token:
        print(f"[CRITICAL] SERVICE_KEY равен None! Проверьте файл .env!")
        return False

    body = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(endpoint, json=body, timeout=5.0)
            if resp.status_code == 200:
                return True
            else:
                print(f"Ошибка: {resp.status_code} {resp.text}")
                return False
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    test_msg = "🛡 Люблю Виту!"
    asyncio.run(send_telegram_alert(test_msg))
