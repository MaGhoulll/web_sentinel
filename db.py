import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_target(url: str, expected_keyword: str):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO targets (url, expected_keyword) VALUES (%s, %s) RETURNING id",
            (url, expected_keyword)
            )
        target_id = cursor.fetchone()
        new_id = target_id[0]
        conn.commit()
        return new_id
    except Exception as e:
        conn.rollback()
        print(f"Возникла ошибка при добавлении объекта: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_active_targets():
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, expected_keyword FROM targets WHERE is_active = TRUE")
        targets = cursor.fetchall()
        return targets
    except Exception as e:
        print(f"Возникла ошибка при получении активных объектов: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_check_result(
        target_id: int,
        status_code:int = None, 
        latency_ms:float = None, 
        is_alive: bool = True, 
        error_message: str = None, 
        ssl_days_left: int = None) -> int | None:
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()
        sql_statement = "INSERT INTO checks (target_id, status_code, latency_ms, is_alive, error_message, ssl_days_left) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;"
        cursor.execute(sql_statement, (target_id, status_code, latency_ms, is_alive, error_message, ssl_days_left))
        conn.commit()
        check_id = cursor.fetchone()[0]
        return check_id
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Возникла ошибка при сохранении результата проверки: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    print(get_active_targets())
    print(save_check_result(target_id=1, status_code=200, latency_ms=123.45, is_alive=True, error_message=None, ssl_days_left=30))
    print(add_target(url="https://example.com", expected_keyword="Example Domain"))