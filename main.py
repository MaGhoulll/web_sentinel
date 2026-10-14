import ssl
import socket
import datetime
from urllib.parse import urlparse
import httpx
import db
import asyncio
import time
from alerts import send_telegram_alert

site_states = {}


async def check_website(
    client: httpx.AsyncClient, url: str, expected_keyword: str = None
):
    try:
        response = await client.get(url, timeout=5, follow_redirects=True)
        latency = response.elapsed.total_seconds() * 1000  # Convert to milliseconds
        if response.status_code == 200 and expected_keyword is not None:
            if expected_keyword in response.text:
                return (response.status_code, round(latency, 2), True, None)
            elif (
                response.status_code == 200
                and expected_keyword is not None
                and expected_keyword not in response.text
            ):
                return (
                    response.status_code,
                    round(latency, 2),
                    False,
                    "Ключевое слово не найдено",
                )
        elif response.status_code == 200 and expected_keyword is None:
            return (response.status_code, round(latency, 2), True, None)
        else:
            return (
                response.status_code,
                round(latency, 2),
                False,
                f"HTTP Error {response.status_code}",
            )
    except httpx.RequestError as exc:
        err_type = type(exc).__name__
        error_msg = f"{err_type}: {exc}" if str(exc) else err_type
        return (None, None, False, error_msg)


def get_ssl_expiration_date(hostname: str, port: int = 443):

    context = ssl.create_default_context()

    try:
        with socket.create_connection((hostname, port), timeout=4) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiration_date = datetime.datetime.strptime(
                    cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                )
                exp_delta = expiration_date - datetime.datetime.now()
                return exp_delta.days

    except Exception as exc:
        return None


async def check_and_save_target(
    client: httpx.AsyncClient, target_id: int, url: str, expected_keyword: str
):
    hostname = urlparse(url).netloc
    ssl_days = await asyncio.to_thread(get_ssl_expiration_date, hostname)
    status_code, latency_ms, is_alive, error_message = await check_website(
        client, url, expected_keyword
    )
    log_id = db.save_check_result(
        target_id=target_id,
        status_code=status_code,
        latency_ms=latency_ms,
        is_alive=is_alive,
        error_message=error_message,
        ssl_days_left=ssl_days,
    )
    print(
        f"[CHECK] Сайт {url} проверен | Статус: {status_code} | Задержка: {latency_ms} ms | Жив: {is_alive} | Ошибка: {error_message} | Дней до истечения SSL сертификата: {ssl_days}"
    )

    if target_id not in site_states:
        site_states[target_id] = {
            "fails": 0,
            "alerted": False,
            "ssl_alerted": False,
        }
    state = site_states[target_id]
    if not is_alive:
        state["fails"] += 1
        if state["fails"] >= 5 and not state["alerted"]:
            msg = f"🚨 <b>[CRITICAL]</b> Сайт {url} недоступен 5 проверок подряд!\nОшибка: <code>{error_message}</code>"
            await send_telegram_alert(msg)
            state["alerted"] = True
    else:
        if state["alerted"]:
            msg = f"<b>[RESOLVED]</b> Работа сайта {url} успешно восстановлена!\nСтатус: <code>{status_code}</code>, Задержка: <code>{latency_ms} ms</code>"
            await send_telegram_alert(msg)
            state["alerted"] = False
        state["fails"] = 0
    if ssl_days is not None and ssl_days <= 50:
        if not state.get("ssl_alerted"):
            ssl_msg = (
                f"<b>[SSL WARNING]</b> Сертификат для {url} истекает через"
                f" <code>{ssl_days}</code> дней!"
            )
            await send_telegram_alert(ssl_msg)
            state["ssl_alerted"] = True


async def main():
    round_number = 1
    sleep_interval_sec = 5
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0")
    }

    if not db.check_db_connection():
        print("\n[CRITICAL] База данных недоступна! Проверьте службу" " PostgreSQL.")
        print("[CRITICAL] Запуск Web Sentinel аварийно остановлен.\n")
        return  # ВЫХОДИМ ИЗ MAIN НЕМЕДЛЕННО!

    print("[SYSTEM] Фоновый движок запущен. Нажмите Ctrl + C для остановки.")

    async with httpx.AsyncClient(headers=headers) as client:
        while True:
            start_time = time.time()
            print(f"\n---> [РАУНД #{round_number}] Старт обработки очереди...")
            targets = db.get_active_targets()

            if targets is None:
                print("\n[FATAL] Потеряно соединение с PostgreSQL во время работы!")
                print("[SHUTDOWN] Аварийная остановка Web Sentinel.\n")
                await send_telegram_alert(
                    "<b>[INFRA CRITICAL]</b> Соединение с базой данных потеряно! Сервис остановлен."
                )
                break

            tasks = []
            for id, url, expected_keyword in targets:
                coro = check_and_save_target(client, id, url, expected_keyword)
                tasks.append(coro)
            results = await asyncio.gather(*tasks)
            print(
                f"Раунд {round_number} завершен. Потраченое время {time.time() - start_time}"
            )
            round_number += 1
            print(f"[SLEEP] Засыпаем на {sleep_interval_sec} секунд...")
            await asyncio.sleep(sleep_interval_sec)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Получен сигнал SIGINT (Ctrl + C). Движок штатно остановлен.")
