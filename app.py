from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any

from flask import Flask, abort, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "snapclass.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = "snapclass-admin-teacher-student-module"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "password_hash" not in user_columns or "role" not in user_columns:
            connection.executescript(
                """
                DROP TABLE IF EXISTS notifications;
                DROP TABLE IF EXISTS assignments;
                DROP TABLE IF EXISTS notes;
                DROP TABLE IF EXISTS marks;
                DROP TABLE IF EXISTS attendance;
                DROP TABLE IF EXISTS classrooms;
                DROP TABLE IF EXISTS courses;
                DROP TABLE IF EXISTS teachers;
                DROP TABLE IF EXISTS students;
                DROP TABLE IF EXISTS users;
                """
            )

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student'))
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                class_name TEXT NOT NULL,
                advisor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_DATE
            );

            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_DATE
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL UNIQUE,
                teacher_name TEXT NOT NULL,
                classroom TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS classrooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                capacity INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available'
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(student_id, course_name, attendance_date)
            );

            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                term TEXT NOT NULL,
                mark INTEGER NOT NULL,
                UNIQUE(student_id, course_name, term)
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT CURRENT_DATE
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course_name TEXT NOT NULL,
                student_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT CURRENT_DATE
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_DATE
            );
            """
        )

        connection.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Admin User", "admin@snapclass.com", generate_password_hash("Admin@123"), "admin"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Teacher User", "teacher@snapclass.com", generate_password_hash("Teacher@123"), "teacher"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Student User", "student@snapclass.com", generate_password_hash("Student@123"), "student"),
        )

        connection.execute(
            "INSERT OR IGNORE INTO students (name, email, class_name, advisor) VALUES (?, ?, ?, ?)",
            ("Aarav Sharma", "aarav@snapclass.com", "Grade 8 Math", "Ms. Patel"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO students (name, email, class_name, advisor) VALUES (?, ?, ?, ?)",
            ("Naira Singh", "naira@snapclass.com", "Grade 8 Math", "Ms. Patel"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO students (name, email, class_name, advisor) VALUES (?, ?, ?, ?)",
            ("Ishita Rao", "ishita@snapclass.com", "Grade 9 Science", "Mr. Raman"),
        )

        connection.execute(
            "INSERT OR IGNORE INTO teachers (name, email, department) VALUES (?, ?, ?)",
            ("Ms. Patel", "ms.patel@snapclass.com", "Mathematics"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO teachers (name, email, department) VALUES (?, ?, ?)",
            ("Mr. Raman", "mr.raman@snapclass.com", "Science"),
        )

        connection.execute(
            "INSERT OR IGNORE INTO courses (name, code, teacher_name, classroom) VALUES (?, ?, ?, ?)",
            ("Grade 8 Math", "MATH-101", "Ms. Patel", "Room A1"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO courses (name, code, teacher_name, classroom) VALUES (?, ?, ?, ?)",
            ("Grade 9 Science", "SCI-204", "Mr. Raman", "Lab 2"),
        )

        connection.execute(
            "INSERT OR IGNORE INTO classrooms (name, capacity, status) VALUES (?, ?, ?)",
            ("Room A1", 30, "Available"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO classrooms (name, capacity, status) VALUES (?, ?, ?)",
            ("Lab 2", 24, "Available"),
        )

        connection.execute(
            "INSERT OR IGNORE INTO attendance (student_id, course_name, attendance_date, status) VALUES (?, ?, ?, ?)",
            (1, "Grade 8 Math", datetime.now().strftime("%Y-%m-%d"), "Present"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO attendance (student_id, course_name, attendance_date, status) VALUES (?, ?, ?, ?)",
            (2, "Grade 8 Math", datetime.now().strftime("%Y-%m-%d"), "Present"),
        )
        connection.execute(
            "INSERT OR IGNORE INTO attendance (student_id, course_name, attendance_date, status) VALUES (?, ?, ?, ?)",
            (3, "Grade 9 Science", datetime.now().strftime("%Y-%m-%d"), "Absent"),
        )

        connection.execute(
            "INSERT OR IGNORE INTO marks (student_id, course_name, term, mark) VALUES (?, ?, ?, ?)",
            (1, "Grade 8 Math", "Term 1", 92),
        )
        connection.execute(
            "INSERT OR IGNORE INTO marks (student_id, course_name, term, mark) VALUES (?, ?, ?, ?)",
            (2, "Grade 8 Math", "Term 1", 88),
        )
        connection.execute(
            "INSERT OR IGNORE INTO marks (student_id, course_name, term, mark) VALUES (?, ?, ?, ?)",
            (3, "Grade 9 Science", "Term 1", 80),
        )

        connection.execute(
            "INSERT OR IGNORE INTO notifications (user_id, message) VALUES (?, ?)",
            (3, "Your assignment submission for Grade 8 Math is due tomorrow."),
        )
        connection.execute(
            "INSERT OR IGNORE INTO notifications (user_id, message) VALUES (?, ?)",
            (3, "Your attendance has improved this week."),
        )

        connection.commit()


initialize_database()


def current_user() -> dict[str, Any] | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_connection() as connection:
        record = connection.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if record is None:
            return None
        return dict(record)


def fetch_students() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("SELECT * FROM students ORDER BY id").fetchall()


def fetch_teachers() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("SELECT * FROM teachers ORDER BY id").fetchall()


def fetch_courses() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("SELECT * FROM courses ORDER BY id").fetchall()


def fetch_classrooms() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("SELECT * FROM classrooms ORDER BY id").fetchall()


def compute_ai_insights() -> list[str]:
    with get_connection() as connection:
        average_mark = connection.execute("SELECT COALESCE(AVG(mark), 0) FROM marks").fetchone()[0]
        attendance_rate = connection.execute(
            "SELECT COALESCE(AVG(CASE WHEN status='Present' THEN 1 ELSE 0 END), 0) FROM attendance"
        ).fetchone()[0]

    insights = []
    if average_mark >= 85:
        insights.append("Top performers are maintaining a strong academic average.")
    else:
        insights.append("Performance can improve with targeted revision sessions.")

    if attendance_rate >= 0.8:
        insights.append("Class attendance is healthy and consistent across the current roster.")
    else:
        insights.append("Attendance needs follow-up to sustain improvement in classroom participation.")

    return insights


@app.route("/")
def home():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    if user["role"] == "teacher":
        return redirect(url_for("teacher_dashboard"))
    return redirect(url_for("student_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_connection() as connection:
            record = connection.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = ?", (email,)).fetchone()
        if record and check_password_hash(record["password_hash"], password):
            session["user_id"] = record["id"]
            session["user_role"] = record["role"]
            session["user_name"] = record["name"]
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin")
def admin_dashboard():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    with get_connection() as connection:
        student_count = connection.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        teacher_count = connection.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
        course_count = connection.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        classroom_count = connection.execute("SELECT COUNT(*) FROM classrooms").fetchone()[0]
        present_count = connection.execute(
            "SELECT COUNT(*) FROM attendance WHERE attendance_date = ? AND status='Present'",
            (datetime.now().strftime("%Y-%m-%d"),),
        ).fetchone()[0]

    stats = [
        {"title": "Students", "value": student_count, "detail": "Managed learners"},
        {"title": "Teachers", "value": teacher_count, "detail": "Active faculty"},
        {"title": "Courses", "value": course_count, "detail": "Academic programs"},
        {"title": "Classrooms", "value": classroom_count, "detail": "Allocated spaces"},
        {"title": "Attendance", "value": present_count, "detail": "Marked today"},
    ]
    return render_template("admin_dashboard.html", user=user, stats=stats)


@app.route("/admin/students", methods=["GET", "POST"])
def admin_students():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        class_name = request.form["class_name"].strip()
        advisor = request.form["advisor"].strip()
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO students (name, email, class_name, advisor) VALUES (?, ?, ?, ?)",
                (name, email, class_name, advisor),
            )
            connection.commit()
        return redirect(url_for("admin_students"))

    students = fetch_students()
    return render_template("admin_students.html", user=user, students=students)


@app.route("/admin/teachers", methods=["GET", "POST"])
def admin_teachers():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        department = request.form["department"].strip()
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO teachers (name, email, department) VALUES (?, ?, ?)",
                (name, email, department),
            )
            connection.commit()
        return redirect(url_for("admin_teachers"))

    teachers = fetch_teachers()
    return render_template("admin_teachers.html", user=user, teachers=teachers)


@app.route("/admin/courses", methods=["GET", "POST"])
def admin_courses():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        code = request.form["code"].strip().upper()
        teacher_name = request.form["teacher_name"].strip()
        classroom = request.form["classroom"].strip()
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO courses (name, code, teacher_name, classroom) VALUES (?, ?, ?, ?)",
                (name, code, teacher_name, classroom),
            )
            connection.commit()
        return redirect(url_for("admin_courses"))

    courses = fetch_courses()
    return render_template("admin_courses.html", user=user, courses=courses)


@app.route("/admin/classrooms", methods=["GET", "POST"])
def admin_classrooms():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        capacity = int(request.form["capacity"])
        status = request.form["status"].strip()
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO classrooms (name, capacity, status) VALUES (?, ?, ?)",
                (name, capacity, status),
            )
            connection.commit()
        return redirect(url_for("admin_classrooms"))

    classrooms = fetch_classrooms()
    return render_template("admin_classrooms.html", user=user, classrooms=classrooms)


@app.route("/admin/reports")
def admin_reports():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT s.name, s.class_name,
                   (SELECT COUNT(*) FROM attendance a WHERE a.student_id = s.id AND a.attendance_date = ? AND a.status='Present') AS present_count
            FROM students s
            ORDER BY s.id
            """,
            (today,),
        ).fetchall()

    return render_template("admin_reports.html", user=user, rows=rows, today=today)


@app.route("/teacher")
def teacher_dashboard():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))

    students = fetch_students()
    insights = compute_ai_insights()
    return render_template("teacher_dashboard.html", user=user, students=students, insights=insights)


@app.route("/teacher/attendance", methods=["GET", "POST"])
def teacher_attendance():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        today = datetime.now().strftime("%Y-%m-%d")
        with get_connection() as connection:
            for key, value in request.form.items():
                if key.startswith("status_"):
                    student_id = int(key.split("_", 1)[1])
                    course_name = request.form.get("course_name", "Grade 8 Math")
                    connection.execute(
                        "INSERT INTO attendance (student_id, course_name, attendance_date, status) VALUES (?, ?, ?, ?) "
                        "ON CONFLICT(student_id, course_name, attendance_date) DO UPDATE SET status=excluded.status",
                        (student_id, course_name, today, value),
                    )
            connection.commit()
        return redirect(url_for("teacher_attendance"))

    students = fetch_students()
    return render_template("teacher_attendance.html", user=user, students=students)


@app.route("/teacher/assignments", methods=["GET", "POST"])
def teacher_assignments():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        course_name = request.form["course_name"].strip()
        student_name = request.form["student_name"].strip()
        file = request.files.get("file")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            with get_connection() as connection:
                connection.execute(
                    "INSERT INTO assignments (title, course_name, student_name, file_name) VALUES (?, ?, ?, ?)",
                    (title, course_name, student_name, filename),
                )
                connection.commit()
        return redirect(url_for("teacher_assignments"))

    assignments = []
    with get_connection() as connection:
        assignments = connection.execute("SELECT * FROM assignments ORDER BY id DESC").fetchall()
    return render_template("teacher_assignments.html", user=user, assignments=assignments)


@app.route("/teacher/notes", methods=["GET", "POST"])
def teacher_notes():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        course_name = request.form["course_name"].strip()
        file = request.files.get("file")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            with get_connection() as connection:
                connection.execute(
                    "INSERT INTO notes (title, course_name, file_name) VALUES (?, ?, ?)",
                    (title, course_name, filename),
                )
                connection.commit()
        return redirect(url_for("teacher_notes"))

    notes = []
    with get_connection() as connection:
        notes = connection.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    return render_template("teacher_notes.html", user=user, notes=notes)


@app.route("/teacher/marks", methods=["GET", "POST"])
def teacher_marks():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        with get_connection() as connection:
            for key, value in request.form.items():
                if key.startswith("mark_"):
                    student_id = int(key.split("_", 1)[1])
                    course_name = request.form.get("course_name", "Grade 8 Math")
                    term = request.form.get("term", "Term 1")
                    connection.execute(
                        "INSERT INTO marks (student_id, course_name, term, mark) VALUES (?, ?, ?, ?) "
                        "ON CONFLICT(student_id, course_name, term) DO UPDATE SET mark=excluded.mark",
                        (student_id, course_name, term, int(value)),
                    )
            connection.commit()
        return redirect(url_for("teacher_marks"))

    students = fetch_students()
    return render_template("teacher_marks.html", user=user, students=students)


@app.route("/teacher/reports")
def teacher_reports():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT s.name, s.class_name,
                   COALESCE((SELECT AVG(mark) FROM marks m WHERE m.student_id = s.id), 0) AS avg_mark,
                   COALESCE((SELECT COUNT(*) FROM attendance a WHERE a.student_id = s.id AND a.status='Present'), 0) AS present_count
            FROM students s
            ORDER BY s.id
            """
        ).fetchall()
    return render_template("teacher_reports.html", user=user, rows=rows)


@app.route("/teacher/insights")
def teacher_insights():
    user = current_user()
    if not user or user["role"] != "teacher":
        return redirect(url_for("login"))
    return render_template("teacher_insights.html", user=user, insights=compute_ai_insights())


@app.route("/student")
def student_dashboard():
    user = current_user()
    if not user or user["role"] != "student":
        return redirect(url_for("login"))

    with get_connection() as connection:
        attendance_rows = connection.execute(
            "SELECT course_name, attendance_date, status FROM attendance WHERE student_id = ? ORDER BY id DESC LIMIT 5",
            (user["id"],),
        ).fetchall()
        mark_rows = connection.execute(
            "SELECT course_name, term, mark FROM marks WHERE student_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
        notifications = connection.execute(
            "SELECT message, created_at FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 5",
            (user["id"],),
        ).fetchall()

    return render_template(
        "student_dashboard.html",
        user=user,
        attendance_rows=attendance_rows,
        mark_rows=mark_rows,
        notifications=notifications,
    )


@app.route("/student/attendance")
def student_attendance():
    user = current_user()
    if not user or user["role"] != "student":
        return redirect(url_for("login"))

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT course_name, attendance_date, status FROM attendance WHERE student_id = ? ORDER BY attendance_date DESC",
            (user["id"],),
        ).fetchall()
    return render_template("student_attendance.html", user=user, rows=rows)


@app.route("/student/notes")
def student_notes():
    user = current_user()
    if not user or user["role"] != "student":
        return redirect(url_for("login"))

    with get_connection() as connection:
        rows = connection.execute("SELECT title, course_name, file_name FROM notes ORDER BY id DESC").fetchall()
    return render_template("student_notes.html", user=user, rows=rows)


@app.route("/student/assignments", methods=["GET", "POST"])
def student_assignments():
    user = current_user()
    if not user or user["role"] != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        course_name = request.form["course_name"].strip()
        file = request.files.get("file")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            with get_connection() as connection:
                connection.execute(
                    "INSERT INTO assignments (title, course_name, student_name, file_name) VALUES (?, ?, ?, ?)",
                    (title, course_name, user["name"], filename),
                )
                connection.commit()
        return redirect(url_for("student_assignments"))

    with get_connection() as connection:
        rows = connection.execute("SELECT title, course_name, student_name, file_name FROM assignments WHERE student_name = ? ORDER BY id DESC", (user["name"],)).fetchall()
    return render_template("student_assignments.html", user=user, rows=rows)


@app.route("/student/marks")
def student_marks():
    user = current_user()
    if not user or user["role"] != "student":
        return redirect(url_for("login"))

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT course_name, term, mark FROM marks WHERE student_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
    return render_template("student_marks.html", user=user, rows=rows)


@app.route("/student/notifications")
def student_notifications():
    user = current_user()
    if not user or user["role"] != "student":
        return redirect(url_for("login"))

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT message, created_at FROM notifications WHERE user_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
    return render_template("student_notifications.html", user=user, rows=rows)


@app.route("/downloads/<path:filename>")
def download_file(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# Existing admin routes to preserve the original project structure
@app.route("/classes", methods=["GET", "POST"])
def classes():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        teacher = request.form["teacher"].strip()
        room = request.form["room"].strip()
        status = request.form["status"]
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO courses (name, code, teacher_name, classroom) VALUES (?, ?, ?, ?)",
                (name, f"AUTO-{int(datetime.now().timestamp())}", teacher, room),
            )
            connection.commit()
        return redirect(url_for("classes"))

    with get_connection() as connection:
        class_rows = connection.execute(
            "SELECT c.name, c.teacher_name AS teacher, c.classroom AS room, 'Active' AS status, 0 AS student_count FROM courses c ORDER BY c.id"
        ).fetchall()
    return render_template("classes.html", classes=class_rows)


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    today = datetime.now().strftime("%Y-%m-%d")
    if request.method == "POST":
        with get_connection() as connection:
            for key, value in request.form.items():
                if key.startswith("status_"):
                    student_id = int(key.split("_", 1)[1])
                    student = connection.execute("SELECT id, name, class_name FROM students WHERE id = ?", (student_id,)).fetchone()
                    if student is None:
                        continue
                    connection.execute(
                        "INSERT INTO attendance (student_id, course_name, attendance_date, status) VALUES (?, ?, ?, ?) "
                        "ON CONFLICT(student_id, course_name, attendance_date) DO UPDATE SET status=excluded.status",
                        (student_id, student["class_name"], today, value),
                    )
            connection.commit()
        return redirect(url_for("report"))

    with get_connection() as connection:
        students = connection.execute("SELECT id, name, class_name FROM students ORDER BY id").fetchall()
    return render_template("attendance.html", students=students, today=datetime.now().strftime("%d %b %Y"))


@app.route("/tasks", methods=["GET", "POST"])
def tasks_page():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        time_text = request.form["time"].strip()
        class_name = request.form["class_name"].strip()
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO notes (title, course_name, file_name) VALUES (?, ?, ?)",
                (title, class_name, f"{title}.txt"),
            )
            connection.commit()
        return redirect(url_for("tasks_page"))

    with get_connection() as connection:
        tasks = connection.execute("SELECT title, course_name AS class_name, uploaded_at AS time FROM notes ORDER BY id").fetchall()
    return render_template("tasks.html", tasks=tasks)


@app.route("/report")
def report():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT c.name AS class_name,
                   (SELECT COUNT(*) FROM students s WHERE s.class_name = c.name) AS student_count,
                   (SELECT COUNT(*) FROM attendance a WHERE a.course_name = c.name AND a.attendance_date = ? AND a.status = 'Present') AS present_count
            FROM courses c
            ORDER BY c.id
            """,
            (today,),
        ).fetchall()

    report_rows = []
    for row in rows:
        student_count = row["student_count"] or 0
        present_count = row["present_count"] or 0
        rate = round((present_count / student_count) * 100, 2) if student_count else 0
        report_rows.append(
            {
                "class_name": row["class_name"],
                "student_count": student_count,
                "present_count": present_count,
                "rate": rate,
            }
        )
    return render_template("report.html", report_rows=report_rows, today=datetime.now().strftime("%d %b %Y"))


@app.route("/reset-db")
def reset_db():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))

    with get_connection() as connection:
        connection.executescript(
            """
            DELETE FROM notifications;
            DELETE FROM assignments;
            DELETE FROM notes;
            DELETE FROM marks;
            DELETE FROM attendance;
            DELETE FROM classrooms;
            DELETE FROM courses;
            DELETE FROM teachers;
            DELETE FROM students;
            DELETE FROM users;
            """
        )
        connection.commit()
    initialize_database()
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
