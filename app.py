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
    cursor.execute("SELECT * FROM exercises ORDER BY muscle_group")
    exercises = cursor.fetchall()
    conn.close()
    return render_template("index.html", exercises=exercises)

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
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)