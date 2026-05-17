import sqlite3

def init_db():
    conn = sqlite3.connect("liftlog.db")
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            muscle_group TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workout_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day_of_week TEXT NOT NULL
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
    """)

    conn.commit()
    conn.close()
    print("Database created successfully!")

if __name__ == "__main__":
    init_db()