import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "liftlog.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

exercises = [
    ("Bench Press", "Chest"),
    ("Incline Dumbbell Press", "Chest"),
    ("Push Up", "Chest"),
    ("Squat", "Legs"),
    ("Leg Press", "Legs"),
    ("Romanian Deadlift", "Legs"),
    ("Pull Up", "Back"),
    ("Barbell Row", "Back"),
    ("Lat Pulldown", "Back"),
    ("Overhead Press", "Shoulders"),
    ("Lateral Raise", "Shoulders"),
    ("Bicep Curl", "Arms"),
    ("Tricep Pushdown", "Arms"),
    ("Plank", "Core"),
    ("Deadlift", "Back"),
]

cursor.executemany(
    "INSERT INTO exercises (name, muscle_group) VALUES (?, ?)",
    exercises
)

conn.commit()
conn.close()
print("Exercises added!")