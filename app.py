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

    # Get all workout dates from the last 2 weeks
    from datetime import date, timedelta
    today = date.today()
    two_weeks_ago = today - timedelta(days=13)
    cursor.execute("""
        SELECT DISTINCT date FROM workout_logs
        WHERE date >= ? AND date <= ?
        ORDER BY date
    """, (two_weeks_ago.isoformat(), today.isoformat()))
    workout_dates = [row["date"] for row in cursor.fetchall()]
    conn.close()
    return render_template("index.html", splits=splits, workout_dates=workout_dates, today=today.isoformat(), two_weeks_ago=two_weeks_ago.isoformat())

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
    name = request.form["name"].title()
    muscle_group = request.form["muscle_group"]
    conn = get_db()
    cursor = conn.cursor()
    # Only insert if exercise name doesn't already exist
    cursor.execute("SELECT id FROM exercises WHERE name = ?", (name,))
    existing = cursor.fetchone()
    if not existing:
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
            ORDER BY split_exercises.exercise_order
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

    # Build preview data for each day
    days_preview = []
    for day in days:
        cursor.execute("""
            SELECT exercises.*, split_exercises.sets_count
            FROM exercises
            JOIN split_exercises ON exercises.id = split_exercises.exercise_id
            WHERE split_exercises.split_day_id = ?
            ORDER BY split_exercises.exercise_order
        """, (day["id"],))
        exercises = cursor.fetchall()

        exercise_previews = []
        total_sets = 0
        for exercise in exercises:
            # Get last session's sets x reps
            cursor.execute("""
                SELECT workout_logs.id FROM workout_logs
                WHERE workout_logs.exercise_id = ?
                ORDER BY workout_logs.date DESC LIMIT 1
            """, (exercise["id"],))
            last_log = cursor.fetchone()

            if last_log:
                cursor.execute("""
                    SELECT COUNT(*) as set_count, ROUND(AVG(reps)) as avg_reps
                    FROM sets WHERE log_id = ?
                """, (last_log["id"],))
                stats = cursor.fetchone()
                sets = stats["set_count"]
                reps = stats["avg_reps"] or 10
            else:
                sets = 1
                reps = 10

            total_sets += sets
            exercise_previews.append({
                "name": exercise["name"],
                "sets": sets,
                "reps": int(reps)
            })

        days_preview.append({
            "id": day["id"],
            "day_name": day["day_name"],
            "day_order": day["day_order"],
            "exercises": exercise_previews,
            "total_sets": total_sets,
            "total_exercises": len(exercise_previews)
        })

    conn.close()
    return render_template("pick_day.html", split=split, days=days_preview)

@app.route("/log/<int:split_id>/<int:day_id>")
def log_day(split_id, day_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workout_splits WHERE id = ?", (split_id,))
    split = cursor.fetchone()
    cursor.execute("SELECT * FROM split_days WHERE id = ?", (day_id,))
    day = cursor.fetchone()
    cursor.execute("""
        SELECT exercises.*, split_exercises.sets_count,
            split_exercises.id as split_exercise_id FROM exercises
        JOIN split_exercises ON exercises.id = split_exercises.exercise_id
        WHERE split_exercises.split_day_id = ?
    """, (day_id,))
    exercises = cursor.fetchall()
    previous_data = {}
    last_unit = "lbs"
    
    # Fetch existing supersets for this day
    cursor.execute("""
        SELECT * FROM supersets WHERE split_day_id = ?
    """, (day_id,))
    superset_rows = cursor.fetchall()
    supersets = {row["exercise_id_1"]: row["exercise_id_2"] for row in superset_rows}
    superset_is_custom = {row["exercise_id_1"]: row["is_custom_superset"] for row in superset_rows}

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
    return render_template("log_day.html", split=split, day=day, exercises=exercises, previous_data=previous_data, last_unit=last_unit, supersets=supersets, superset_is_custom=superset_is_custom)

@app.route("/log/<int:split_id>/<int:day_id>", methods=["POST"])
def save_day_workout(split_id, day_id):
    date = request.form["date"]
    conn = get_db()
    cursor = conn.cursor()

    # Step 1: create any new exercises added during this session (negative temp IDs)
    temp_id_map = {}  # maps temp negative id -> real new exercise id
    for key in request.form:
        if key.startswith("new_exercise_"):
            temp_id = key.replace("new_exercise_", "")
            name, muscle_group = request.form[key].split("|")
            cursor.execute(
                "INSERT INTO exercises (name, muscle_group) VALUES (?, ?)",
                (name, muscle_group)
            )
            new_exercise_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO split_exercises (split_day_id, exercise_id, sets_count) VALUES (?, ?, ?)",
                (day_id, new_exercise_id, 1)
            )
            temp_id_map[temp_id] = new_exercise_id

    # Step 2: get all real exercises for this day (including the ones just created)
    cursor.execute("""
        SELECT exercises.* FROM exercises
        JOIN split_exercises ON exercises.id = split_exercises.exercise_id
        WHERE split_exercises.split_day_id = ?
    """, (day_id,))
    exercises = cursor.fetchall()
    real_exercise_ids = [str(e["id"]) for e in exercises]

    # Step 3: save sets for each exercise — checking both real ids and temp ids
    for exercise in exercises:
        exercise_id = exercise["id"]
        # Find if this exercise has form data under its real id or a temp id that maps to it
        form_id = str(exercise_id)
        for temp_id, real_id in temp_id_map.items():
            if real_id == exercise_id:
                form_id = temp_id

        if f"weight_{form_id}_1" not in request.form:
            continue  # skip exercises with no sets logged (shouldn't normally happen)

        cursor.execute(
            "INSERT INTO workout_logs (exercise_id, date) VALUES (?, ?)",
            (exercise_id, date)
        )
        log_id = cursor.lastrowid
        set_number = 1
        while f"weight_{form_id}_{set_number}" in request.form:
            weight = request.form[f"weight_{form_id}_{set_number}"]
            reps = request.form[f"reps_{form_id}_{set_number}"]
            unit = request.form.get("unit", "lbs")
            cursor.execute(
                "INSERT INTO sets (log_id, set_number, reps, weight, unit) VALUES (?, ?, ?, ?, ?)",
                (log_id, set_number, reps, weight, unit)
            )
            set_number += 1

    # Step 4: handle explicitly deleted supersets first
    deleted_supersets = request.form.getlist("deleted_superset")
    for exercise_id_1 in deleted_supersets:
        cursor.execute("SELECT * FROM supersets WHERE split_day_id = ? AND exercise_id_1 = ?", (day_id, exercise_id_1))
        superset = cursor.fetchone()
        if superset:
            if superset["is_custom_superset"] == 1:
                cursor.execute("DELETE FROM split_exercises WHERE exercise_id = ? AND split_day_id = ?", (superset["exercise_id_2"], day_id))
                cursor.execute("DELETE FROM exercises WHERE id = ?", (superset["exercise_id_2"],))
            cursor.execute("DELETE FROM supersets WHERE split_day_id = ? AND exercise_id_1 = ?", (day_id, exercise_id_1))

    # Save remaining supersets, converting any temp ids to their real new ids
    cursor.execute("DELETE FROM supersets WHERE split_day_id = ?", (day_id,))
    superset_pairs = request.form.getlist("superset_pair")
    for pair in superset_pairs:
        ex1, ex2 = pair.split("_")
        # Check if ex2 was a newly added custom exercise (was a temp negative id)
        is_custom = 1 if ex2 in temp_id_map else 0
        if ex1 in temp_id_map:
            ex1 = temp_id_map[ex1]
        if ex2 in temp_id_map:
            ex2 = temp_id_map[ex2]
        cursor.execute(
            "INSERT INTO supersets (split_day_id, exercise_id_1, exercise_id_2, is_custom_superset) VALUES (?, ?, ?, ?)",
            (day_id, ex1, ex2, is_custom)
        )

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

    # Get exercise info
    cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
    exercise = cursor.fetchone()

    # Current max — highest weight from most recent session
    cursor.execute("""
        SELECT MAX(sets.weight) as max_weight
        FROM sets
        JOIN workout_logs ON sets.log_id = workout_logs.id
        WHERE workout_logs.exercise_id = ?
        AND workout_logs.date = (
            SELECT MAX(date) FROM workout_logs WHERE exercise_id = ?
        )
    """, (exercise_id, exercise_id))
    current_max_row = cursor.fetchone()
    current_max = current_max_row["max_weight"] if current_max_row["max_weight"] else 0

    # All-time best — highest weight ever
    cursor.execute("""
        SELECT MAX(sets.weight) as max_weight
        FROM sets
        JOIN workout_logs ON sets.log_id = workout_logs.id
        WHERE workout_logs.exercise_id = ?
    """, (exercise_id,))
    all_time_row = cursor.fetchone()
    all_time_best = all_time_row["max_weight"] if all_time_row["max_weight"] else 0

    # Strength graph — max weight per session
    cursor.execute("""
        SELECT workout_logs.date, MAX(sets.weight) as max_weight
        FROM workout_logs
        JOIN sets ON sets.log_id = workout_logs.id
        WHERE workout_logs.exercise_id = ?
        GROUP BY workout_logs.date
        ORDER BY workout_logs.date
    """, (exercise_id,))
    strength_rows = cursor.fetchall()

    # Reps graph — total reps per session
    cursor.execute("""
        SELECT workout_logs.date, SUM(sets.reps) as total_reps
        FROM workout_logs
        JOIN sets ON sets.log_id = workout_logs.id
        WHERE workout_logs.exercise_id = ?
        GROUP BY workout_logs.date
        ORDER BY workout_logs.date
    """, (exercise_id,))
    reps_rows = cursor.fetchall()

    # Volume graph — weight x reps per session
    cursor.execute("""
        SELECT workout_logs.date, SUM(sets.weight * sets.reps) as volume
        FROM workout_logs
        JOIN sets ON sets.log_id = workout_logs.id
        WHERE workout_logs.exercise_id = ?
        GROUP BY workout_logs.date
        ORDER BY workout_logs.date
    """, (exercise_id,))
    volume_rows = cursor.fetchall()

    conn.close()
    return render_template("exercise_graph.html",
        exercise=exercise,
        current_max=current_max,
        all_time_best=all_time_best,
        strength_dates=[r["date"] for r in strength_rows],
        strength_values=[r["max_weight"] for r in strength_rows],
        reps_dates=[r["date"] for r in reps_rows],
        reps_values=[r["total_reps"] for r in reps_rows],
        volume_dates=[r["date"] for r in volume_rows],
        volume_values=[r["volume"] for r in volume_rows]
    )

@app.route("/log/<int:split_id>/<int:day_id>/remove-exercise/<int:split_exercise_id>", methods=["POST"])
def remove_exercise_from_log(split_id, day_id, split_exercise_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM split_exercises WHERE id = ?",
        (split_exercise_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("log_day", split_id=split_id, day_id=day_id))

@app.route("/split/<int:split_id>/reorder-exercises", methods=["POST"])
def reorder_exercises(split_id):
    data = request.get_json()
    split_exercise_ids = data.get("order", [])
    conn = get_db()
    cursor = conn.cursor()
    for index, split_exercise_id in enumerate(split_exercise_ids):
        cursor.execute(
            "UPDATE split_exercises SET exercise_order = ? WHERE id = ?",   
            (index, split_exercise_id)
        )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.route("/log/<int:split_id>/<int:day_id>/remove-superset/<int:exercise_id_1>", methods=["POST"])
def remove_superset(split_id, day_id, exercise_id_1):
    conn = get_db()
    cursor = conn.cursor()

    # Find the superset row first
    cursor.execute("""
        SELECT * FROM supersets WHERE split_day_id = ? AND exercise_id_1 = ?
    """, (day_id, exercise_id_1))
    superset = cursor.fetchone()

    if superset:
        if superset["is_custom_superset"] == 1:
            # Case 2: custom exercise — delete from split_exercises and exercises entirely
            cursor.execute(
                "DELETE FROM split_exercises WHERE exercise_id = ? AND split_day_id = ?",
                (superset["exercise_id_2"], day_id)
            )
            cursor.execute(
                "DELETE FROM exercises WHERE id = ?",
                (superset["exercise_id_2"],)
            )
        # Both cases: delete the superset pair itself
        cursor.execute(
            "DELETE FROM supersets WHERE split_day_id = ? AND exercise_id_1 = ?",
            (day_id, exercise_id_1)
        )

    conn.commit()
    conn.close()
    return redirect(url_for("log_day", split_id=split_id, day_id=day_id))

@app.route("/calendar-data")
def calendar_data():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all distinct workout dates
    cursor.execute("""
        SELECT DISTINCT date FROM workout_logs ORDER BY date
    """)
    all_dates = [row["date"] for row in cursor.fetchall()]
    
    # Get workout details per date
    workout_details = {}
    for date in all_dates:
        cursor.execute("""
            SELECT split_days.day_name, COUNT(DISTINCT workout_logs.id) as exercise_count,
                   COUNT(sets.id) as total_sets
            FROM workout_logs
            JOIN sets ON sets.log_id = workout_logs.id
            LEFT JOIN split_days ON split_days.id = (
                SELECT split_exercises.split_day_id FROM split_exercises
                WHERE split_exercises.exercise_id = workout_logs.exercise_id
                LIMIT 1
            )
            WHERE workout_logs.date = ?
        """, (date,))
        details = cursor.fetchone()
        if details:
            workout_details[date] = {
                "day_name": details["day_name"] or "Workout",
                "total_sets": details["total_sets"] or 0,
                "exercise_count": details["exercise_count"] or 0
            }
    
    conn.close()
    from flask import jsonify
    return jsonify({
        "workout_dates": all_dates,
        "workout_details": workout_details
    })

if __name__ == "__main__":
    app.run(debug=True)