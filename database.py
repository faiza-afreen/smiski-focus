 
import sqlite3
import csv
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager


BASE_DIR = Path(__file__).parent

DB_FILE = BASE_DIR / "smiski.db"
CSV_FILE = BASE_DIR / "distractions.csv"


# Connect to the database
@contextmanager
def connect():

    conn = sqlite3.connect(DB_FILE, timeout=10)

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# Create database tables
def init_db():

    with connect() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS distractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_minutes REAL NOT NULL,
                completed INTEGER NOT NULL,
                distractions INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)


# Transfer old CSV records into SQLite
def migrate_csv():

    with connect() as conn:

        conn.execute("BEGIN IMMEDIATE")

        migrated = conn.execute("""
            SELECT value FROM metadata
            WHERE key = 'csv_migrated'
        """).fetchone()

        if migrated:

            print("CSV records already migrated.")
            return

        if not CSV_FILE.exists():

            print("No existing CSV file found.")
            return

        count = 0

        with open(
            CSV_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                website = row.get("website")
                timestamp = row.get("timestamp")

                if website and timestamp:

                    conn.execute("""
                        INSERT INTO distractions
                        (website, timestamp)
                        VALUES (?, ?)
                    """, (website, timestamp))

                    count += 1

        conn.execute("""
            INSERT INTO metadata (key, value)
            VALUES ('csv_migrated', 'true')
        """)

        print(f"Successfully migrated {count} records!")


# Record a new distraction
def add_distraction(website="Instagram"):

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    with connect() as conn:

        conn.execute("""
            INSERT INTO distractions
            (website, timestamp)
            VALUES (?, ?)
        """, (website, timestamp))

    return timestamp


# Count all recorded distractions
def count_distractions():

    with connect() as conn:

        result = conn.execute("""
            SELECT COUNT(*) FROM distractions
            WHERE website = 'Instagram'
        """).fetchone()

        return result[0]


# Record a focus session
def add_study_session(
    start_time,
    end_time,
    duration_minutes,
    completed,
    distractions
):

    with connect() as conn:

        conn.execute("""
            INSERT INTO study_sessions (
                start_time,
                end_time,
                duration_minutes,
                completed,
                distractions
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            start_time,
            end_time,
            duration_minutes,
            int(completed),
            distractions
        ))


# Retrieve all distractions
def get_distractions():

    with connect() as conn:

        return conn.execute("""
            SELECT * FROM distractions
            ORDER BY timestamp DESC
        """).fetchall()


# Retrieve all study sessions
def get_study_sessions():

    with connect() as conn:

        return conn.execute("""
            SELECT * FROM study_sessions
            ORDER BY start_time DESC
        """).fetchall()


# Initialize database when run directly
if __name__ == "__main__":

    init_db()
    migrate_csv()

    print("Smiski Database is ready!")
    print(f"Database location: {DB_FILE}")
    print(f"Total distractions: {count_distractions()}")
    print(f"Total study sessions: {len(get_study_sessions())}")
