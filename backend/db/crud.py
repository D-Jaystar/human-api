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


def get_recent_activities(device_id: str, limit: int = 10) -> list[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM activity_logs WHERE device_id = ? ORDER BY start_time DESC LIMIT ?
            """,
                (device_id, limit)
        )
        return cursor.fetchall()


def log_health_metric(
        device_id: str,
        metric_type: str,
        value: float,
        recorded_at: str,
) -> int | None:
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO health_metrics (device_id, metric_type, value, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (device_id, metric_type, value, recorded_at),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error:
        return None


def get_health_metric(
        device_id: str,
        metric_type: str | None = None,
        limit: int = 10,
) -> list[sqlite3.Row]:
    with get_db_connection() as conn:
        if metric_type:
            cursor = conn.execute(
                """
                SELECT * FROM health_metrics WHERE device_id = ? AND metric_type = ?
                ORDER BY recorded_at DESC LIMIT ?
                """,
                (device_id, metric_type, limit),
            )
        else: cursor = conn.execute(
            """
            SELECT * FROM health_metrics WHERE device_id = ?
            ORDER BY recorded_at DESC LIMIT ?
            """,
            (device_id, limit),

        )
        return cursor.fetchall()





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

if __name__ == "__main__":
    # Test 1: Activiteit loggen
    log_id = log_activity(
        device_id="pc-01",
        app_name="IntelliJ IDEA",
        window_title="crud.py - human_api",
        is_afk=False,
        start_time="2026-11-05T17:30:00",
        end_time="2026-11-05T17:40:00",
        duration_sec=600,
    )
    print(f"Activiteit opgeslagen met log ID: {log_id}")

    # Test 2: Recente activiteiten ophalen
    logs = get_recent_activities("pc-01", limit=5)
    print(f"Aantal logs opgehaald: {len(logs)}")
    for log in logs:
        print(f"- {log['app_name']} | {log['window_title']} ({log['duration_sec']}s)")

    # Test 4: Health metric opslaan
    health_id = log_health_metric("pc-01", "steps", 8450.0, "2026-11-06T20:30:00")
    print(f"Health metric opgeslagen met ID: {health_id}")

    # Test 5: Health metrics ophalen (alles)
    metrics = get_health_metric("pc-01")
    for m in metrics:
        print(f"- {m['metric_type']}: {m['value']} op {m['recorded_at']}")