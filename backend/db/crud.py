import sqlite3
from database import get_db_connection

def register_device(device_id: str, name: str, token_hash: str) -> bool:
    try:
        with get_db_connection() as db_connection:
            cursor = db_connection.cursor()
            cursor.execute(
                "INSERT INTO devices (id, name, token_hash) VALUES (?, ?, ?)",
                (device_id, name, token_hash),
            )
            db_connection.commit()

        return True
    except sqlite3.IntegrityError:
        return False


def get_device(device_id: str) -> sqlite3.Row | None:
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM devices WHERE id = ?",
            (device_id,),
        )
        return cursor.fetchone()

def log_activity(
        device_id: str,
        app_name: str,
        window_title: str,
        is_afk: bool,
        start_time: str,
        end_time: str,
        duration_sec: int,
) -> int | None:
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO activity_logs (device_id, app_name, window_title, is_afk, start_time, end_time, duration_sec)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (device_id, app_name, window_title, int(is_afk), start_time, end_time, duration_sec),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error:
        return None




if __name__ == "__main__":
    # Test 1: Registreren
    succes = register_device("pc-01", "Laptop Werk", "hash123")
    print(f"Device geregistreerd: {succes}")

    # Test 2: Ophalen
    device = get_device("pc-01")
    if device:
        print(f"Gevonden apparaat: {device['name']} met ID {device['id']}")
    else:
        print("Niet gevonden")

    # Test 3: Activiteit loggen
    log_id = log_activity("pc-01", "Chrome", "PortSwigger Academy", False, "2026-11-05 23:00", "2026-11-05 23:15", 900)
    print(f"Log ID: {log_id}")