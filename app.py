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

    # Get search term (trim whitespace)
    q = request.args.get("q", "").strip()

    # Base query (used for both list and search)
    base_query = """
        SELECT DISTINCT
            s.student_id, s.first_name, s.last_name,s.email,
            s.date_of_birth, s.phone, s.enrollment_date
        FROM students s
      
    """

    # If the user clicked "Search" but submitted an empty query,
    # show an info message and fall back to displaying all students.
    if "q" in request.args and q == "":
        flash("No search term entered. Showing all students.", "info")

    # If there is a non-empty search term, filter by first/last name (partial match)
    if q != "":
        query = base_query + """
            WHERE s.first_name LIKE %s OR s.last_name LIKE %s
            ORDER BY s.last_name, s.first_name
        """
        cursor.execute(query, (f"%{q}%", f"%{q}%"))
    else:
        # Otherwise, show all students (alphabetical order)
    
        query = base_query + """
            ORDER BY s.last_name, s.first_name
        """
        cursor.execute(query)

    students = cursor.fetchall()
    # If a search was performed but no results found, show a warning message
    if q and len(students) == 0:
       flash("No students matched your search.", "warning")
    cursor.close()

    return render_template("student_list.html", students=students)


@app.route("/classes")
def class_list():
    cursor = db.get_cursor()

    # Query to display:
    # - all classes (even if no students enrolled)
    # - shown by Dance Type and in grade order， considering NULL grades as lowest
    # - and any enrolled students listed under each class
    query = """
    SELECT
        c.class_id AS class_id,
        c.class_name AS class_name,
        c.schedule_day AS schedule_day,
        c.schedule_time AS schedule_time,
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
    ORDER BY dt.dancetype_name,  (g.grade_level IS NULL), g.grade_level, c.class_name, s.last_name, s.first_name;
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




# Student Class Summary
@app.route('/student/class-summary')
def student_class_summary():

    sid = request.args.get('student_id')
    if not sid:
        return redirect(url_for('student_list'))

    cur = db.get_cursor()

    # --------------------------------------------------
    # 1) Retrieve basic student information
    #    This confirms the student exists and provides
    #    data for the page heading.
    # --------------------------------------------------
    cur.execute("""
        SELECT
            student_id,
            first_name,
            last_name,
            email,
            phone,
            date_of_birth
        FROM students
        WHERE student_id = %s;
    """, (sid,))
    student = cur.fetchone()

    # If the student does not exist, return to student list
    if not student:
        cur.close()
        return redirect(url_for('student_list'))

    # --------------------------------------------------
    # 2) Retrieve all classes the student is enrolled in
    #    Listing requirements match the Class List:
    #    - grouped by Dance Type
    #    - ordered by grade level (NULL grades last)
    #    - then by class name
    # --------------------------------------------------
    cur.execute("""
        SELECT
            c.class_id AS class_id,
            c.class_name AS class_name,
            c.schedule_day AS schedule_day,
            c.schedule_time AS schedule_time,
            dt.dancetype_name AS dance_type,
            g.grade_level AS grade_level,
            g.grade_name AS grade_name
        FROM studentclasses sc
        JOIN classes c ON c.class_id = sc.class_id
        JOIN dancetype dt ON c.dancetype_id = dt.dancetype_id
        LEFT JOIN grades g ON c.grade_id = g.grade_id
        WHERE sc.student_id = %s
        ORDER BY
            dt.dancetype_name,
            (g.grade_level IS NULL),
            g.grade_level,
            c.class_name;
    """, (sid,))
    classes = cur.fetchall()
    cur.close()

    # 3) Handle case where student has no enrolled classes
 
    if not classes:
        flash("This student is not enrolled in any classes.", "warning")
  
    return render_template("student_class_summary.html",student=student,classes=classes)

  
  
    

@app.route('/student/enrol', methods=['GET', 'POST'])
def student_enrol():

    # ===== POST: save enrolment =====
    if request.method == 'POST':
        sid = request.form.get('student_id')
        class_id = request.form.get('class_id')

        if not sid or not class_id:
            flash('Please select a student and a class.')
            return redirect(url_for('student_list'))

        cur = db.get_cursor()

        # Insert enrolment (studentclasses has a UNIQUE (student_id, class_id) constraint)
        # so duplicates are prevented at the database level as well.
        try:
            cur.execute("""
                INSERT INTO studentclasses (student_id, class_id)
                VALUES (%s, %s);
            """, (sid, class_id))
            # Commit here if your connection is not autocommit
            # db.connection.commit()
        except Exception:
            # If a duplicate is attempted, the UNIQUE constraint will raise an error.
            # We can safely ignore and redirect back.
            pass

        cur.close()
        return redirect(url_for('student_class_summary', student_id=sid))

    # ===== GET: display enrolment form =====
    sid = request.args.get('student_id')
    if not sid:
        return redirect(url_for('student_list'))

    cur = db.get_cursor()

    # Retrieve student basic info (for page heading)
    cur.execute("""
        SELECT student_id, first_name, last_name
        FROM students
        WHERE student_id=%s;
    """, (sid,))
    student = cur.fetchone()

    if not student:
        cur.close()
        return redirect(url_for('student_list'))

    # Retrieve eligible classes:
    # - Student must be qualified in the same dance type at the class grade level
    #   OR one grade level above
    # - Exclude classes the student is already enrolled in
    cur.execute("""
        SELECT
            c.class_id,
            c.class_name,
            dt.dancetype_name,
            g.grade_level,
            g.grade_name,
            c.schedule_day,
            c.schedule_time
        FROM classes c
        JOIN dancetype dt ON c.dancetype_id = dt.dancetype_id
        LEFT JOIN grades g ON c.grade_id = g.grade_id
        WHERE
          EXISTS (
            SELECT 1
            FROM studentgrades sg
            JOIN grades gg ON sg.grade_id = gg.grade_id
            JOIN grades cg ON c.grade_id = cg.grade_id
            WHERE sg.student_id = %s
              AND sg.dancetype_id = c.dancetype_id
              AND cg.grade_level IN (gg.grade_level, gg.grade_level + 1)
          )
          AND NOT EXISTS (
            SELECT 1
            FROM studentclasses sc
            WHERE sc.student_id = %s AND sc.class_id = c.class_id
          )
        ORDER BY dt.dancetype_name, g.grade_level, c.class_name;
    """, (sid, sid))
    eligible_classes = cur.fetchall()

    cur.close()

    return render_template(
        'student_enrol.html',
        student=student,
        eligible_classes=eligible_classes
    )



@app.route('/teachers/report')
def teacher_report():
    cur = db.get_cursor()

    # Teachers -> Classes -> Studentclasses (LEFT JOIN keeps teachers even if no classes/students)
    cur.execute("""
        SELECT
            t.teacher_id,
            t.first_name,
            t.last_name,
            c.class_id,
            c.class_name,
            COUNT(sc.student_id) AS student_count
        FROM teachers t
        LEFT JOIN classes c ON c.teacher_id = t.teacher_id
        LEFT JOIN studentclasses sc ON sc.class_id = c.class_id
        GROUP BY t.teacher_id, t.first_name, t.last_name, c.class_id, c.class_name
        ORDER BY t.last_name, t.first_name, c.class_name;
    """)
    rows = cur.fetchall()

    cur.execute("""
        SELECT
            t.teacher_id,
            COUNT(DISTINCT sc.student_id) AS total_students
        FROM teachers t
        LEFT JOIN classes c ON c.teacher_id = t.teacher_id
        LEFT JOIN studentclasses sc ON sc.class_id = c.class_id
        GROUP BY t.teacher_id;
    """)
    totals = {r['teacher_id']: r['total_students'] for r in cur.fetchall()}

    cur.close()

    # Build report structure for template
    report = []
    current_tid = None
    teacher_block = None

    for r in rows:
        tid = r['teacher_id']

        if current_tid != tid:
            current_tid = tid
            teacher_block = {
                'teacher_id': tid,
                'first_name': r['first_name'],
                'last_name': r['last_name'],
                'total_students': totals.get(tid, 0),
                'classes': []
            }
            report.append(teacher_block)

        if r['class_id'] is not None:
            teacher_block['classes'].append({
                'class_name': r['class_name'],
                'student_count': r['student_count']
            })

    return render_template("teacher_report.html", report=report)
