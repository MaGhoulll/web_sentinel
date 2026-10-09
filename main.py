import ssl
import socket
import datetime
from urllib.parse import urlparse
import httpx
import db

def check_website(url: str, expected_keyword: str = None):
    try:
        client = httpx.Client(timeout=5.0, follow_redirects=True)
        response = client.get(url, timeout=5, follow_redirects=True)
        latency = response.elapsed.total_seconds() * 1000  # Convert to milliseconds
        if response.status_code == 200 and expected_keyword is not None:
            if expected_keyword in response.text:
                return (response.status_code, round(latency, 2), True, None)
            elif response.status_code == 200 and expected_keyword is not None and expected_keyword not in response.text:
                return (response.status_code, round(latency, 2), False, 'Ключевое слово не найдено')
        elif response.status_code == 200 and expected_keyword is None:
            return (response.status_code, round(latency, 2), True, None)
        else:
            return (response.status_code, round(latency, 2), False, f"HTTP Error {response.status_code}")
    except httpx.RequestError as exc:
        return (None, None, False, str(exc))

def get_ssl_expiration_date(hostname: str, port: int = 443):
    
    context = ssl.create_default_context()

    try:
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiration_date = datetime.datetime.strptime(
                    cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                )
                exp_delta = expiration_date - datetime.datetime.now()
                return exp_delta.days

    except Exception as exc:
        return None

targets = db.get_active_targets()
for id, url, expected_keyword in targets:
    hostname = urlparse(url).netloc
    ssl_days_left = get_ssl_expiration_date(hostname)
    status_code, latency_ms, is_alive, error_message = check_website(url, expected_keyword)

    db.save_check_result(target_id=id, status_code=status_code, latency_ms=latency_ms, is_alive=is_alive, error_message=error_message, ssl_days_left=ssl_days_left)
    print(f"[CHECK] Сайт {url} проверен | Статус: {status_code} | Задержка: {latency_ms} ms | Жив: {is_alive} | Ошибка: {error_message} | Дней до истечения SSL сертификата: {ssl_days_left}")