import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "liftlog.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workout_splits ORDER BY id")
    splits = cursor.fetchall()
    conn.close()
    return render_template("index.html", splits=splits)

@app.route("/exercises")
def exercises():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exercises ORDER BY muscle_group")
    exercises = cursor.fetchall()
    conn.close()
    return render_template("exercises.html", exercises=exercises)

@app.route("/add-exercise", methods=["POST"])
def add_exercise():
    name = request.form["name"]
    muscle_group = request.form["muscle_group"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO exercises (name, muscle_group) VALUES (?, ?)",
        (name, muscle_group)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("exercises"))

@app.route("/create-split")
def create_split():
    return render_template("create_split.html")

@app.route("/create-split", methods=["POST"])
def save_split():
    split_name = request.form["split_name"].title()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workout_splits (name) VALUES (?)",
        (split_name,)
    )
    split_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return redirect(url_for("view_split", split_id=split_id))

@app.route("/split/<int:split_id>")
def view_split(split_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workout_splits WHERE id = ?", (split_id,))
    split = cursor.fetchone()
    cursor.execute(
        "SELECT * FROM split_days WHERE split_id = ? ORDER BY day_order",
        (split_id,)
    )
    days = cursor.fetchall()
    days_with_exercises = []
    for day in days:
        cursor.execute("""
            SELECT exercises.*, split_exercises.sets_count,
                   split_exercises.id as split_exercise_id
            FROM exercises
            JOIN split_exercises ON exercises.id = split_exercises.exercise_id
            WHERE split_exercises.split_day_id = ?
        """, (day["id"],))
        day_exercises = cursor.fetchall()
        days_with_exercises.append({
            "id": day["id"],
            "day_name": day["day_name"],
            "day_order": day["day_order"],
            "exercises": day_exercises
        })
    conn.close()
    return render_template("view_split.html", split=split, days=days_with_exercises)

@app.route("/split/<int:split_id>/add-day", methods=["POST"])
def add_day(split_id):
    day_name = request.form["day_name"].title()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM split_days WHERE split_id = ?",
        (split_id,)
    )
    day_count = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO split_days (split_id, day_name, day_order) VALUES (?, ?, ?)",
        (split_id, day_name, day_count + 1)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("view_split", split_id=split_id))

@app.route("/split/<int:split_id>/add-day-exercise/<int:day_id>")
def add_day_exercise_page(split_id, day_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM split_days WHERE id = ?", (day_id,))
    day = cursor.fetchone()
    cursor.execute("""
        SELECT exercises.*, split_exercises.sets_count FROM exercises
        JOIN split_exercises ON exercises.id = split_exercises.exercise_id
        WHERE split_exercises.split_day_id = ?
    """, (day_id,))
    current_exercises = cursor.fetchall()
    cursor.execute("SELECT * FROM exercises ORDER BY muscle_group")
    all_exercises = cursor.fetchall()
    conn.close()
    return render_template("add_day_exercise.html",
        day=day,
        split_id=split_id,
        current_exercises=current_exercises,
        all_exercises=all_exercises
    )

@app.route("/split/<int:split_id>/add-day-exercise/<int:day_id>", methods=["POST"])
def save_day_exercise(split_id, day_id):
    exercise_id = request.form["exercise_id"]
    sets_count = request.form["sets_count"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO split_exercises (split_day_id, exercise_id, sets_count) VALUES (?, ?, ?)",
        (day_id, exercise_id, sets_count)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("add_day_exercise_page", split_id=split_id, day_id=day_id))

@app.route("/log-workout")
def log_workout():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exercises ORDER BY name")
    exercises = cursor.fetchall()
    conn.close()
    return render_template("log_workout.html", exercises=exercises)

@app.route("/log-workout", methods=["POST"])
def save_workout():
    exercise_id = request.form["exercise_id"]
    date = request.form["date"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workout_logs (exercise_id, date) VALUES (?, ?)",
        (exercise_id, date)
    )
    log_id = cursor.lastrowid
    set_number = 1
    while f"weight_{set_number}" in request.form:
        weight = request.form[f"weight_{set_number}"]
        reps = request.form[f"reps_{set_number}"]
        cursor.execute(
            "INSERT INTO sets (log_id, set_number, reps, weight) VALUES (?, ?, ?, ?)",
            (log_id, set_number, reps, weight)
        )
        set_number += 1
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

@app.route("/log/<int:split_id>")
def pick_day(split_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workout_splits WHERE id = ?", (split_id,))
    split = cursor.fetchone()
    cursor.execute(
        "SELECT * FROM split_days WHERE split_id = ? ORDER BY day_order",
        (split_id,)
    )
    days = cursor.fetchall()
    conn.close()
    return render_template("pick_day.html", split=split, days=days)

@app.route("/log/<int:split_id>/<int:day_id>")
def log_day(split_id, day_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workout_splits WHERE id = ?", (split_id,))
    split = cursor.fetchone()
    cursor.execute("SELECT * FROM split_days WHERE id = ?", (day_id,))
    day = cursor.fetchone()
    cursor.execute("""
        SELECT exercises.*, split_exercises.sets_count FROM exercises
        JOIN split_exercises ON exercises.id = split_exercises.exercise_id
        WHERE split_exercises.split_day_id = ?
    """, (day_id,))
    exercises = cursor.fetchall()
    previous_data = {}
    last_unit = "lbs"
    for exercise in exercises:
        cursor.execute("""
            SELECT workout_logs.id, workout_logs.date
            FROM workout_logs
            WHERE workout_logs.exercise_id = ?
            ORDER BY workout_logs.date DESC
            LIMIT 1
        """, (exercise["id"],))
        last_log = cursor.fetchone()
        if last_log:
            cursor.execute("""
                SELECT set_number, weight, reps, unit
                FROM sets
                WHERE log_id = ?
                ORDER BY set_number
            """, (last_log["id"],))
            sets = cursor.fetchall()
            previous_data[exercise["id"]] = {
                "date": last_log["date"],
                "sets": sets
            }
            if sets:
                last_unit = sets[0]["unit"]
    conn.close()
    return render_template("log_day.html", split=split, day=day,
                           exercises=exercises, previous_data=previous_data,
                           last_unit=last_unit)

@app.route("/log/<int:split_id>/<int:day_id>", methods=["POST"])
def save_day_workout(split_id, day_id):
    date = request.form["date"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT exercises.* FROM exercises
        JOIN split_exercises ON exercises.id = split_exercises.exercise_id
        WHERE split_exercises.split_day_id = ?
    """, (day_id,))
    exercises = cursor.fetchall()
    for exercise in exercises:
        exercise_id = exercise["id"]
        cursor.execute(
            "INSERT INTO workout_logs (exercise_id, date) VALUES (?, ?)",
            (exercise_id, date)
        )
        log_id = cursor.lastrowid
        set_number = 1
        while f"weight_{exercise_id}_{set_number}" in request.form:
            weight = request.form[f"weight_{exercise_id}_{set_number}"]
            reps = request.form[f"reps_{exercise_id}_{set_number}"]
            unit = request.form.get("unit", "lbs")
            cursor.execute(
                "INSERT INTO sets (log_id, set_number, reps, weight, unit) VALUES (?, ?, ?, ?, ?)",
                (log_id, set_number, reps, weight, unit)
            )
            set_number += 1
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

@app.route("/split/<int:split_id>/add-custom-exercise/<int:day_id>", methods=["POST"])
def add_custom_exercise(split_id, day_id):
    name = request.form["name"].title()
    muscle_group = request.form["muscle_group"]
    sets_count = request.form["sets_count"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO exercises (name, muscle_group) VALUES (?, ?)",
        (name, muscle_group)
    )
    exercise_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO split_exercises (split_day_id, exercise_id, sets_count) VALUES (?, ?, ?)",
        (day_id, exercise_id, sets_count)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("add_day_exercise_page", split_id=split_id, day_id=day_id))

@app.route("/progress")
def progress():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")
    muscle_groups = [row["muscle_group"] for row in cursor.fetchall()]
    charts = []
    for muscle_group in muscle_groups:
        cursor.execute("""
            SELECT workout_logs.date,
                   SUM(sets.weight * sets.reps) as volume
            FROM workout_logs
            JOIN exercises ON workout_logs.exercise_id = exercises.id
            JOIN sets ON sets.log_id = workout_logs.id
            WHERE exercises.muscle_group = ?
            GROUP BY workout_logs.date
            ORDER BY workout_logs.date
        """, (muscle_group,))
        rows = cursor.fetchall()
        if rows:
            charts.append({
                "muscle_group": muscle_group,
                "dates": [row["date"] for row in rows],
                "volumes": [row["volume"] for row in rows]
            })
    conn.close()
    return render_template("progress.html", charts=charts)

@app.route("/split/<int:split_id>/remove-exercise/<int:day_id>/<int:split_exercise_id>", methods=["POST"])
def remove_exercise(split_id, day_id, split_exercise_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM split_exercises WHERE id = ?",
        (split_exercise_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("view_split", split_id=split_id))

@app.route("/split/<int:split_id>/delete", methods=["POST"])
def delete_split(split_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM split_exercises WHERE split_day_id IN (SELECT id FROM split_days WHERE split_id = ?)", (split_id,))
    cursor.execute("DELETE FROM split_days WHERE split_id = ?", (split_id,))
    cursor.execute("DELETE FROM workout_splits WHERE id = ?", (split_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

@app.route("/exercise/<int:exercise_id>/graph")
def exercise_graph(exercise_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
    exercise = cursor.fetchone()
    cursor.execute("""
        SELECT workout_logs.date,
               SUM(sets.weight * sets.reps) as volume
        FROM workout_logs
        JOIN sets ON sets.log_id = workout_logs.id
        WHERE workout_logs.exercise_id = ?
        GROUP BY workout_logs.date
        ORDER BY workout_logs.date
    """, (exercise_id,))
    rows = cursor.fetchall()
    dates = [row["date"] for row in rows]
    volumes = [row["volume"] for row in rows]
    conn.close()
    return render_template("exercise_graph.html", exercise=exercise, dates=dates, volumes=volumes)

if __name__ == "__main__":
    app.run(debug=True)