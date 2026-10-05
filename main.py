import httpx
def check_website(url, expected_keyword: str = None):
    try:
        response = httpx.get(url, timeout=5, follow_redirects=True)
        latency = response.elapsed.total_seconds() * 1000  # Convert to milliseconds
        if response.status_code == 200 and expected_keyword is not None:
            if expected_keyword in response.text:
                return f"[OK] {url} доступен. Статус код: {response.status_code}. Время отклика: {round(latency, 2)} мс. Ключевое слово '{expected_keyword}' найдено."
            else:
                return f"[WARNING] {url} доступен. Статус код: {response.status_code}. Время отклика: {round(latency, 2)} мс. Ключевое слово '{expected_keyword}' не найдено."
        elif response.status_code == 200 and expected_keyword is None:
            return f"[OK] {url} доступен. Статус код: {response.status_code}. Время отклика: {round(latency, 2)} мс."
        else:
            return f"[ERROR] {url} недоступен. Статус код: {response.status_code}. Время отклика: {round(latency, 2)} мс."
    except httpx.RequestError as exc:
        return f"[ERROR] Ошибка при попытке доступа к {url}: {exc}"

print(check_website("https://github.com", expected_keyword="NeSushestvuet123"))