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

active_targets = get_active_targets()
for id, url, expected_keyword in active_targets:
    print(f'ID: {id}, URL: {url}, Expected Keyword: {expected_keyword}')

print("[DEBUG] Проверка .env: DB_USER =", os.getenv("DB_USER"))