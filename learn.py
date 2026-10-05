import ssl
import socket
import datetime
import httpx

hostname = "www.example.com"
port = 443


def get_ssl_expiration_date(hostname: str, port: int):
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
        print(f"[SSL ERROR] Не удалось проверить сертификат для {hostname}: {exc}")


days_remaining = get_ssl_expiration_date(hostname, 443)
print(f"Дней до истечения SSL сертификата для {hostname}: {days_remaining}")
