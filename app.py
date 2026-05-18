import sqlite3
import os
from flask import Flask, render_template

app = Flask(__name__)

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), "liftlog.db")
    conn = sqlite3.connect(db_path)
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

if __name__ == "__main__":
    app.run(debug=True)