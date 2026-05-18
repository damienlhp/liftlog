import sqlite3

conn = sqlite3.connect("liftlog.db")
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