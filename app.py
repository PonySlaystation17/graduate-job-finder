from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


@app.route("/")
def home():
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, company, location, score, salary_min, salary_max, source, url
        FROM jobs
        WHERE applied = 0
        AND active = 1
        ORDER BY score DESC
        LIMIT 10
    """)

    jobs = cursor.fetchall()
    connection.close()

    return render_template("index.html", jobs=jobs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)