import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "liftlog.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            muscle_group TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workout_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS split_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            split_id INTEGER NOT NULL,
            day_name TEXT NOT NULL,
            day_order INTEGER NOT NULL,
            FOREIGN KEY (split_id) REFERENCES workout_splits(id)
        );

        CREATE TABLE IF NOT EXISTS split_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            split_day_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            sets_count INTEGER NOT NULL DEFAULT 3,
            FOREIGN KEY (split_day_id) REFERENCES split_days(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );

        CREATE TABLE IF NOT EXISTS workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );

        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id INTEGER NOT NULL,
            set_number INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            weight REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT 'lbs',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (log_id) REFERENCES workout_logs(id)
        );

        CREATE TABLE IF NOT EXISTS supersets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            split_day_id INTEGER NOT NULL,
            exercise_id_1 INTEGER NOT NULL,
            exercise_id_2 INTEGER NOT NULL,
            FOREIGN KEY (split_day_id) REFERENCES split_days(id),
            FOREIGN KEY (exercise_id_1) REFERENCES exercises(id),
            FOREIGN KEY (exercise_id_2) REFERENCES exercises(id)
        );
                         
    """)

    conn.commit()
    conn.close()
    print(f"Database created at: {DB_PATH}")

if __name__ == "__main__":
    init_db()