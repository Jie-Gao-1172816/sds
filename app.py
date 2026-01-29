from email import errors
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
import db
import connect
from datetime import date, datetime


app = Flask(__name__)
app.secret_key = 'sds_secret_2025'  # Set a secret key for session/flash

# Initialize database connection
db.init_db(
    app, connect.dbuser, connect.dbpass, connect.dbhost, connect.dbname, connect.dbport
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/teachers", methods=["GET"])
def teacher_list():
    cursor = db.get_cursor()
    # List all teachers        
    querystr = "SELECT teacher_id, first_name, last_name FROM teachers;" 
    cursor.execute(querystr)        
    teachers = cursor.fetchall()
    cursor.close()
    if True:  # Example condition for a flash message
        flash("Example of a flash message. Optional, but good for error or confirmation " \
            "messages when used with an IF statement.", "info")
    return render_template("teacher_list.html", teachers=teachers)


@app.route("/students")
def student_list():
    cursor = db.get_cursor()

    q = request.args.get("q")

    if q:
        query = """
        SELECT s.student_id, s.first_name, s.last_name, s.email, s.date_of_birth, s.phone, s.enrollment_date, sc.class_id
        FROM students s
        JOIN studentclasses sc ON s.student_id = sc.student_id
        WHERE s.first_name LIKE %s OR s.last_name LIKE %s
        ORDER BY s.last_name, s.first_name
        """
        cursor.execute(query, (f"%{q}%", f"%{q}%"))
    else:
        query = """
        SELECT s.student_id, s.first_name, s.last_name, s.email, s.date_of_birth, s.phone, s.enrollment_date, sc.class_id
        FROM students s
        JOIN studentclasses sc ON s.student_id = sc.student_id
        ORDER BY s.last_name, s.first_name
        """
        cursor.execute(query)

    students = cursor.fetchall()
    cursor.close()

    return render_template("student_list.html", students=students)

@app.route("/classes")
def class_list():
    cursor = db.get_cursor()
    query = """
    SELECT
        c.class_id AS class_id,
        c.class_name AS class_name,
        dt.dancetype_name AS dance_type,
        g.grade_level AS grade_level,
        g.grade_name AS grade_name,
        s.student_id AS student_id,
        s.first_name AS first_name,
        s.last_name AS last_name
    FROM classes c
    JOIN dancetype dt ON c.dancetype_id = dt.dancetype_id
    LEFT JOIN grades g ON c.grade_id = g.grade_id
    LEFT JOIN studentclasses sc ON c.class_id = sc.class_id
    LEFT JOIN students s ON sc.student_id = s.student_id
    ORDER BY dt.dancetype_name, g.grade_level, c.class_name, s.last_name, s.first_name;
    """
    cursor.execute(query)
    classes = cursor.fetchall()
    cursor.close()

    return render_template("class_list.html", classes=classes)




# edit student
@app.route('/student/edit', methods=['GET', 'POST'])
def edit_student():
    if request.method == 'POST':
        # ===== UPDATE (edit existing student) =====
        sid = request.form.get('student_id')

        first_name = request.form.get('first_name')
        last_name  = request.form.get('last_name')
        email      = request.form.get('email') or None
        phone      = request.form.get('phone') or None
        dob        = request.form.get('date_of_birth') or None

        cur = db.get_cursor()
        cur.execute("""
            UPDATE students
            SET first_name=%s, last_name=%s, email=%s, phone=%s, date_of_birth=%s
            WHERE student_id=%s;
        """, (first_name, last_name, email, phone, dob, sid))
        cur.close()

        return redirect(url_for('student_list'))

    # ===== GET: show form =====
    sid = request.args.get('student_id')

    if sid is None:
        # Add page (blank)
        return render_template(
            'student_edit.html',
            edit=False,
            student={'enrollment_date': date.today().isoformat()},
            today=date.today().isoformat()
        )
    else:
        # Edit page (load from DB)
        cur = db.get_cursor()
        cur.execute("""
            SELECT student_id, first_name, last_name, email, phone, date_of_birth, enrollment_date
            FROM students
            WHERE student_id=%s;
        """, (sid,))
        student = cur.fetchone()
        cur.close()

        return render_template(
            'student_edit.html',
            edit=True,
            student=student,
            today=date.today().isoformat()
        )


# POST only: INSERT (add new student)
@app.route('/student/add', methods=['POST'])
def add_student():
    first_name = request.form.get('first_name')
    last_name  = request.form.get('last_name')
    email      = request.form.get('email') or None
    phone      = request.form.get('phone') or None
    dob        = request.form.get('date_of_birth') or None

    # enrollment_date: if blank, set to today (先简单)
    enrollment_date = request.form.get('enrollment_date') or date.today().isoformat()

    cur = db.get_cursor()
    cur.execute("""
        INSERT INTO students (first_name, last_name, email, phone, date_of_birth, enrollment_date)
        VALUES (%s,%s,%s,%s,%s,%s);
    """, (first_name, last_name, email, phone, dob, enrollment_date))
    cur.close()

    return redirect(url_for('student_list'))

# Add other routes and view functions as required.
@app.route("/students/<int:student_id>")
def class_summary(student_id):
    return f"Class summary for student {student_id}"

