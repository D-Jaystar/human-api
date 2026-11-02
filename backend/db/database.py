import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# DRY-principe: bereken de hoofdmap (human_api/) dynamisch vanaf dit bestand
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
DB_PATH: Path = BASE_DIR / "human_api.db"
BACKUP_DIR: Path = BASE_DIR / "backups"


def get_db_connection() -> sqlite3.Connection:
    """
    Maakt een SQLite Connection Instance aan met Write-Ahead Logging (WAL)
    en Foreign Key ondersteuning.
    """
    conn: sqlite3.Connection = sqlite3.connect(DB_PATH)
    # Zorgt dat we kolommen straks op naam kunnen uitlezen (bijv. row["app_name"])
    conn.row_factory = sqlite3.Row

    # Activeer WAL-mode en Foreign Keys
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def create_backup() -> Path | None:
    """
    Maakt een veilige backup van het databasebestand voordat er wijzigingen plaatsvinden.
    """
    # Guard Clause (Early Return): stop direct als het databasebestand nog niet bestaat
    if not DB_PATH.exists():
        print("[INFO] Nog geen database gevonden om te backuppen.")
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file: Path = BACKUP_DIR / f"human_api_backup_{timestamp}.db"

    shutil.copy2(DB_PATH, backup_file)
    print(f"[BACKUP] Database veiliggesteld in: {backup_file.name}")
    return backup_file
def init_db() -> None:
    """
    Initialiseert alle tabellen in SQLite en maakt vooraf een backup.
    """
    create_backup()

    # Context Manager sluit de database-connectie automatisch na afloop
    with get_db_connection() as conn:
        cursor: sqlite3.Cursor = conn.cursor()

        # 1. Devices tabel
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS devices (
                                                              id TEXT PRIMARY KEY,
                                                              name TEXT NOT NULL,
                                                              token_hash TEXT NOT NULL
                       );
                       """)

        # 2. Activity Logs tabel
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS activity_logs (
                                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                    device_id TEXT NOT NULL,
                                                                    app_name TEXT NOT NULL,
                                                                    window_title TEXT NOT NULL,
                                                                    is_afk INTEGER NOT NULL DEFAULT 0,
                                                                    start_time TEXT NOT NULL,
                                                                    end_time TEXT NOT NULL,
                                                                    duration_sec INTEGER NOT NULL,
                                                                    FOREIGN KEY (device_id) REFERENCES devices (id)
                           );
                       """)

        # 3. Hourly Stats tabel
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS hourly_stats (
                                                                   hour_bucket TEXT PRIMARY KEY,
                                                                   active_sec INTEGER NOT NULL DEFAULT 0,
                                                                   afk_sec INTEGER NOT NULL DEFAULT 0,
                                                                   context_switches INTEGER NOT NULL DEFAULT 0,
                                                                   top_app TEXT,
                                                                   fragmentation_rate REAL NOT NULL DEFAULT 0.0
                       );
                       """)

        # 4. Health Metrics tabel
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS health_metrics (
                                                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                     device_id TEXT NOT NULL,
                                                                     metric_type TEXT NOT NULL,
                                                                     value REAL NOT NULL,
                                                                     recorded_at TEXT NOT NULL,
                                                                     FOREIGN KEY (device_id) REFERENCES devices (id)
                           );
                       """)

        conn.commit()
        print("[OK] Alle tabellen succesvol aangemaakt in WAL-mode.")


if __name__ == "__main__":
    init_db()