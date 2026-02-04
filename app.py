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
    app, connect.dbuser, connect.dbpass, connect.dbhost, connect.dbname, connect.dbport)


# ==============================
# Form Validation 
# ==============================

# Helper function to get DOB limits
from datetime import date

def get_dob_limits():
    """
    DOB limits for HTML date picker.
    - min: today - 20 years
    - max: today - 1 year  (student must be at least 1 year old)
    Returns (dob_min, dob_max) as ISO strings.
    """
    today = date.today()

    # min_dob: today - 20 years
    try:
        min_dob = date(today.year - 20, today.month, today.day)
    except ValueError:
        min_dob = date(today.year - 20, today.month, 28)

    # max_dob: today - 1 year
    try:
        max_dob = date(today.year - 1, today.month, today.day)
    except ValueError:
        max_dob = date(today.year - 1, today.month, 28)

    return min_dob.isoformat(), max_dob.isoformat()

def validate_student_form(form):
    """
    Validation shared by Add + Edit.
    Returns (clean_data, errors)

    Rules :
    - first_name / last_name: required; min length 2; letters only (spaces, hyphen, apostrophe allowed); max length 50
    - email: optional; basic format check (no regex)
    - phone: must contain at least 6 digits if provided
    - date_of_birth: REQUIRED; must be valid date; sensible range (today-20 years to today)
    - enrollment_date: defaults to today; if provided, cannot be future
    """
    errors = []

    # Names (required, clearer messages, no regex)
    first_name = (form.get('first_name') or '').strip()
    last_name  = (form.get('last_name') or '').strip()

    def validate_name(value: str, label: str):
        """Basic name rules without regex."""
        if not value:
            errors.append(f"{label} is required.")
            return

        # Minimum length (teacher example: 'B' is not OK)
        if len(value) < 2:
            errors.append(f"{label} must be at least 2 characters.")
            return

        if len(value) > 50:
            errors.append(f"{label} must be 50 characters or fewer.")
            return

        if any(ch.isdigit() for ch in value):
            errors.append(f"{label} cannot contain numbers.")
            return

        # Allow letters plus space, hyphen, apostrophe
        allowed_extra = set(" -'")
        for ch in value:
            if ch.isalpha() or ch in allowed_extra:
                continue
            errors.append(f"{label} can only contain letters, spaces, hyphens, or apostrophes.")
            return

    validate_name(first_name, "First name")
    validate_name(last_name, "Last name")

    # Email (optional, no regex, clearer reasons)
    email = (form.get('email') or '').strip()
    if email:
        if email.count("@") != 1:
            errors.append("Email must contain one '@'.")
        else:
            local, domain = email.split("@")
            if not local:
                errors.append("Email is missing the part before '@'.")
            elif not domain:
                errors.append("Email is missing the domain after '@'.")
            elif domain.startswith(".") or domain.endswith("."):
                errors.append("Email domain cannot start or end with a dot '.'.")
            elif "." not in domain:
                errors.append("Email domain must contain a dot (e.g., example.com).")

    # Phone (simple digit count rule)
    phone = (form.get('phone') or '').strip()
    if phone:
        digits_only = "".join(ch for ch in phone if ch.isdigit())
        if len(digits_only) < 6:
            errors.append("Phone must contain at least 6 digits.")

    # Date of Birth (REQUIRED; sensible range)
    dob_raw = (form.get('date_of_birth') or '').strip()
    dob = None

    if not dob_raw:
        errors.append("Date of birth is required.")
    else:
        try:
            dob = datetime.strptime(dob_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date of birth must be in YYYY-MM-DD format.")
        else:
            today = date.today()

            # Sensible range assumption for assignment
            # minimum: today minus 20 years; maximum: 1 years  old
            try:
                min_dob = date(today.year - 20, today.month, today.day)
            except ValueError:
                # Handle leap day edge case (Feb 29)
                min_dob = date(today.year - 20, today.month, 28)
            
            try:
                max_dob = date(today.year - 1, today.month, today.day)
            except ValueError:
                # Handle leap day edge case (Feb 29)
                max_dob = date(today.year - 1, today.month, 28)


            if dob > max_dob:
                errors.append("Student must be at least 1 year old.")
            elif dob < min_dob:
                errors.append("Date of birth must be within the last 20 years.")
                

    # Enrollment Date (default today, cannot be future)
    enrollment_date_raw = (form.get('enrollment_date') or '').strip()
    if enrollment_date_raw:
        try:
            ed = datetime.strptime(enrollment_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Enrollment date must be in YYYY-MM-DD format.")
            enrollment_date = None
        else:
            if ed > date.today():
                errors.append("Enrollment date cannot be in the future.")
                enrollment_date = None
            else:
                enrollment_date = ed.isoformat()
    else:
        enrollment_date = date.today().isoformat()

    clean = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email or None,
        "phone": phone or None,
        "date_of_birth": dob.isoformat() if dob else None,
        "enrollment_date": enrollment_date
    }

    return clean, errors






# ==============================
# Home Page
# ==============================

@app.route("/")
def home():
    """Display home page"""
    return render_template("home.html")


# ==============================
# Teacher List
# ==============================

@app.route("/teachers", methods=["GET"])
def teacher_list():
    """Display list of all teachers"""
    cursor = db.get_cursor()

    # Retrieve basic teacher information
    querystr = """
        SELECT teacher_id, first_name, last_name, email, phone
        FROM teachers;
    """
    cursor.execute(querystr)
    teachers = cursor.fetchall()
    cursor.close()

    return render_template("teacher_list.html", teachers=teachers)


# ==============================
# Student List + Search
# ==============================

@app.route("/students")
def student_list():
    """
    Display student list.
    Supports optional name search using query parameter `q`.
    """
    cursor = db.get_cursor()

    # Get search term (trim whitespace)
    q = request.args.get("q", "").strip()

    # Base query for student listing
    base_query = """
        SELECT DISTINCT
            s.student_id,
            s.first_name,
            s.last_name,
            s.email,
            s.date_of_birth,
            s.phone,
            s.enrollment_date
        FROM students s
    """

    # User clicked search with empty input
    if "q" in request.args and q == "":
        flash("No search term entered. Showing all students.", "info")

    # Apply search filter if provided
    if q != "":
        query = base_query + """
            WHERE s.first_name LIKE %s OR s.last_name LIKE %s
            ORDER BY s.last_name, s.first_name;
        """
        cursor.execute(query, (f"%{q}%", f"%{q}%"))
    else:
        # Default: show all students alphabetically
        query = base_query + """
            ORDER BY s.last_name, s.first_name;
        """
        cursor.execute(query)

    students = cursor.fetchall()

    # Search performed but no results found
    if q and len(students) == 0:
        flash("No students matched your search.", "warning")

    cursor.close()
    return render_template("student_list.html", students=students)




# ==============================
# Class List
# ==============================

@app.route("/classes")
def class_list():
    """
    Display all classes and enrolled students.
    Classes are ordered by dance type and grade level.
    """
    cursor = db.get_cursor()
    # Retrieve class and student information
    query = """
        SELECT
            c.class_id,
            c.class_name,
            c.schedule_day,
            c.schedule_time,
            dt.dancetype_name,
            g.grade_level,
            g.grade_name,
            s.student_id,
            s.first_name,
            s.last_name
        FROM classes c
        JOIN dancetype dt ON c.dancetype_id = dt.dancetype_id
        LEFT JOIN grades g ON c.grade_id = g.grade_id
        LEFT JOIN studentclasses sc ON c.class_id = sc.class_id
        LEFT JOIN students s ON sc.student_id = s.student_id
        ORDER BY
            dt.dancetype_name,
            (g.grade_level IS NULL),
            g.grade_level,
            c.class_name,
            s.last_name,
            s.first_name;
    """

    cursor.execute(query)
    classes = cursor.fetchall()
    cursor.close()

    return render_template("class_list.html", classes=classes)




# ==============================
#    Edit Student
# ==============================


@app.route('/student/edit', methods=['GET', 'POST'])
def edit_student():
    
    today = date.today().isoformat()
    dob_min, dob_max = get_dob_limits()

    # ---------- POST: update ----------
    if request.method == 'POST':
        sid = request.form.get('student_id')

        # Validate form input
        clean, errors = validate_student_form(request.form)

        # If there are validation errors, re-render the form (do NOT redirect),
        # so the user's correct inputs are preserved.
        if errors:
            for e in errors:
                flash(e, "danger")

            cur = db.get_cursor()

            # Dropdown data
            cur.execute("""
                SELECT grade_id, grade_name, grade_level
                FROM grades
                ORDER BY grade_level, grade_name;
            """)
            grades = cur.fetchall()

            cur.execute("""
                SELECT dancetype_id, dancetype_name
                FROM dancetype
                ORDER BY dancetype_name;
            """)
            dancetypes = cur.fetchall()

            # Rebuild student_grades from submitted form (preserve selections)
            student_grades = {}
            for dt in dancetypes:
                raw = (request.form.get(f"grade_{dt['dancetype_id']}") or "").strip()
                if raw.isdigit():
                    student_grades[dt['dancetype_id']] = int(raw)

            cur.close()

            # Preserve user-entered values in the form
            # enrollment_date is read-only in Edit, but we keep it for display.
            student = {"student_id": sid, "enrollment_date": request.form.get("enrollment_date")}
            student.update(clean)

            return render_template(
                'student_edit.html',
                edit=True,
                student=student,
                today=today,
                dob_min=dob_min,
                dob_max=dob_max,
                grades=grades,
                dancetypes=dancetypes,
                student_grades=student_grades
            )

        cur = db.get_cursor()

        # Edit cannot change enrollment_date (date joined)
        cur.execute("""
            UPDATE students
            SET first_name=%s, last_name=%s, email=%s, phone=%s, date_of_birth=%s
            WHERE student_id=%s;
        """, (
            clean["first_name"], clean["last_name"], clean["email"],
            clean["phone"], clean["date_of_birth"], sid
        ))

        # Replace grades (simple approach: delete then insert)
        cur.execute("DELETE FROM studentgrades WHERE student_id=%s;", (sid,))

        cur.execute("SELECT dancetype_id FROM dancetype;")
        dt_ids = [r["dancetype_id"] for r in cur.fetchall()]

        for dtid in dt_ids:
            raw = (request.form.get(f"grade_{dtid}") or "").strip()
            if raw == "":
                continue
            try:
                gid = int(raw)
            except ValueError:
                continue

            cur.execute("""
                INSERT INTO studentgrades (student_id, dancetype_id, grade_id)
                VALUES (%s, %s, %s);
            """, (sid, dtid, gid))

        cur.close()
        flash("Student updated successfully.", "success")
        return redirect(url_for('student_list'))

    # ---------- GET: show form ----------
    sid = request.args.get('student_id')
    if not sid:
        return redirect(url_for('student_list'))

    cur = db.get_cursor()

    # Load student details
    cur.execute("""
        SELECT student_id, first_name, last_name, email, phone, date_of_birth, enrollment_date
        FROM students
        WHERE student_id=%s;
    """, (sid,))
    student = cur.fetchone()

    # Dropdown options
    cur.execute("""
        SELECT grade_id, grade_name, grade_level
        FROM grades
        ORDER BY grade_level, grade_name;
    """)
    grades = cur.fetchall()

    cur.execute("""
        SELECT dancetype_id, dancetype_name
        FROM dancetype
        ORDER BY dancetype_name;
    """)
    dancetypes = cur.fetchall()

    # Current grade selections for this student
    cur.execute("""
        SELECT dancetype_id, grade_id
        FROM studentgrades
        WHERE student_id=%s;
    """, (sid,))
    student_grades = {r["dancetype_id"]: r["grade_id"] for r in cur.fetchall()}

    cur.close()

    return render_template(
        'student_edit.html',
        edit=True,
        student=student,
        today=today,
        dob_min=dob_min,
        dob_max=dob_max,
        grades=grades,
        dancetypes=dancetypes,
        student_grades=student_grades)





# ==============================
# Add New Student 
# ==============================

@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
   
    today = date.today().isoformat()
    dob_min, dob_max = get_dob_limits()

    # ---------- POST: insert ----------
    if request.method == 'POST':
        clean, errors = validate_student_form(request.form)

        # If there are validation errors, re-render the form (do NOT redirect),
        # so the user's correct inputs are preserved.
        if errors:
            for e in errors:
                flash(e, "danger")

            cur = db.get_cursor()

            cur.execute("""
                SELECT grade_id, grade_name, grade_level
                FROM grades
                ORDER BY grade_level, grade_name;
            """)
            grades = cur.fetchall()

            cur.execute("""
                SELECT dancetype_id, dancetype_name
                FROM dancetype
                ORDER BY dancetype_name;
            """)
            dancetypes = cur.fetchall()

            # Preserve grade selections from submitted form
            student_grades = {}
            for dt in dancetypes:
                raw = (request.form.get(f"grade_{dt['dancetype_id']}") or "").strip()
                if raw.isdigit():
                    student_grades[dt['dancetype_id']] = int(raw)

            cur.close()

            # Preserve user-entered values
            student = {}
            student.update(clean)

            return render_template(
                'student_edit.html',
                edit=False,
                student=student,
                today=today,
                dob_min=dob_min,
                dob_max=dob_max,
                grades=grades,
                dancetypes=dancetypes,
                student_grades=student_grades
            )

        cur = db.get_cursor()

        # Insert new student (student_id is auto generated by DB)
        cur.execute("""
            INSERT INTO students (first_name, last_name, email, phone, date_of_birth, enrollment_date)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            clean["first_name"], clean["last_name"], clean["email"],
            clean["phone"], clean["date_of_birth"], clean["enrollment_date"]
        ))
        new_sid = cur.lastrowid

        # Insert any selected grades
        cur.execute("SELECT dancetype_id FROM dancetype;")
        dt_ids = [r["dancetype_id"] for r in cur.fetchall()]

        for dtid in dt_ids:
            raw = (request.form.get(f"grade_{dtid}") or "").strip()
            if raw == "":
                continue
            try:
                gid = int(raw)
            except ValueError:
                continue

            cur.execute("""
                INSERT INTO studentgrades (student_id, dancetype_id, grade_id)
                VALUES (%s, %s, %s);
            """, (new_sid, dtid, gid))

        cur.close()
        flash("Student added successfully.", "success")
        return redirect(url_for('student_list'))

    # ---------- GET: show form ----------
    cur = db.get_cursor()

    cur.execute("""
        SELECT grade_id, grade_name, grade_level
        FROM grades
        ORDER BY grade_level, grade_name;
    """)
    grades = cur.fetchall()

    cur.execute("""
        SELECT dancetype_id, dancetype_name
        FROM dancetype
        ORDER BY dancetype_name;
    """)
    dancetypes = cur.fetchall()

    cur.close()

    return render_template(
        'student_edit.html',
        edit=False,
        student={},
        today=today,
        dob_min=dob_min,
        dob_max=dob_max,
        grades=grades,
        dancetypes=dancetypes,
        student_grades={})







# ==============================
# Student Class Summary
# ==============================

@app.route('/student/class-summary')
def student_class_summary():

    # Step 1: Get student ID from query string
    sid = request.args.get('student_id')
    if not sid:
        return redirect(url_for('student_list'))

    cur = db.get_cursor()

    # --------------------------------------------------
    # Step 2: Retrieve basic student information
    # Used for page heading and validation
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

    # If student does not exist, return to list
    if not student:
        cur.close()
        return redirect(url_for('student_list'))

    # --------------------------------------------------
    # Step 3: Retrieve student's current grades (studentgrades)
    # This shows the student's current grade per dance type
    # --------------------------------------------------
    cur.execute("""
        SELECT
            dt.dancetype_name,
            g.grade_level,
            g.grade_name
        FROM studentgrades sg
        JOIN dancetype dt ON sg.dancetype_id = dt.dancetype_id
        JOIN grades g ON sg.grade_id = g.grade_id
        WHERE sg.student_id = %s
        ORDER BY
            dt.dancetype_name,
            g.grade_level;
    """, (sid,))
    current_grades = cur.fetchall()

    # --------------------------------------------------
    # Step 4: Retrieve classes the student is enrolled in
    # Ordering:
    # - Dance type
    # - Grade level (NULL last)
    # - Class name
    # --------------------------------------------------
    cur.execute("""
        SELECT
            c.class_id,
            c.class_name,
            c.schedule_day,
            c.schedule_time,
            dt.dancetype_name,
            g.grade_level,
            g.grade_name
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

    # Step 5: Handle case where student has no classes
    if not classes:
        flash("This student is not enrolled in any classes.", "warning")

    return render_template(
        "student_class_summary.html",
        student=student,
        classes=classes,
        current_grades=current_grades)


  
  
    

# ==============================
# Student Enrolment
# ==============================

import MySQLdb

@app.route('/student/enrol', methods=['GET', 'POST'])
def student_enrol():
   
    # ----- POST: Save enrolment -----
    if request.method == 'POST':
        sid = request.form.get('student_id')
        class_id = request.form.get('class_id')

        # Basic validation
        if not sid or not class_id:
            flash('Please select a student and a class.', 'danger')
            return redirect(url_for('student_list'))

        cur = db.get_cursor()

        # Insert enrolment
        # UNIQUE constraint on (student_id, class_id) prevents duplicates
        try:
            cur.execute("""
                INSERT INTO studentclasses (student_id, class_id)
                VALUES (%s, %s);
            """, (sid, class_id))

            # IMPORTANT: commit so the insert is saved
            db.get_db().commit()

            # Success message
            flash('Enrolment saved successfully.', 'success')

        except MySQLdb.IntegrityError:
            # Duplicate enrolment (violates UNIQUE(student_id, class_id))
            db.get_db().rollback()
            flash('This student is already enrolled in that class.', 'warning')

        except Exception as e:
            # Other DB error
            db.get_db().rollback()
            flash(f'Enrolment failed: {e}', 'danger')
            print("ENROL ERROR:", e, flush=True)

        cur.close()
        return redirect(url_for('student_class_summary', student_id=sid))

    # ----- GET: Display enrolment form -----
    sid = request.args.get('student_id')
    if not sid:
        return redirect(url_for('student_list'))

    cur = db.get_cursor()

    # Step 1: Retrieve student basic info
    cur.execute("""
        SELECT student_id, first_name, last_name
        FROM students
        WHERE student_id=%s;
    """, (sid,))
    student = cur.fetchone()

    if not student:
        cur.close()
        return redirect(url_for('student_list'))

    # Step 2: Retrieve eligible classes
    # Rules:
    # - Same dance type
    # - Current grade level OR one level above
    # - Exclude already enrolled classes
    #
    # Note:
    # studentgrades may contain multiple grade records per dance type,
    # so we treat the CURRENT grade as the highest grade_level per dance type.
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
        JOIN grades g ON c.grade_id = g.grade_id

        -- Student's current grade per dance type (highest grade_level)
        JOIN (
            SELECT
                sg.dancetype_id,
                MAX(gr2.grade_level) AS cur_level
            FROM studentgrades sg
            JOIN grades gr2 ON sg.grade_id = gr2.grade_id
            WHERE sg.student_id = %s
            GROUP BY sg.dancetype_id
        ) sgl
          ON sgl.dancetype_id = c.dancetype_id

        -- Exclude already enrolled classes
        LEFT JOIN studentclasses sc
          ON sc.student_id = %s
         AND sc.class_id = c.class_id

        WHERE sc.class_id IS NULL
          AND g.grade_level BETWEEN sgl.cur_level AND (sgl.cur_level + 1)

        ORDER BY dt.dancetype_name, g.grade_level, c.class_name;
    """, (sid, sid))
    eligible_classes = cur.fetchall()

    # Debug (optional)
    print("DEBUG eligible_classes:", eligible_classes, flush=True)

    cur.close()

    return render_template(
        'student_enrol.html',
        student=student,
        eligible_classes=eligible_classes)







# ==============================
# Teacher Report
# ==============================

@app.route('/teachers/report')
def teacher_report():
    """
    Display teacher report showing:
    - Classes taught by each teacher
    - Student count per class
    - Total unique students per teacher
    """

    cur = db.get_cursor()

    # --------------------------------------------------
    # Query 1: Student count per class per teacher
    # LEFT JOIN ensures teachers appear even without classes
    # --------------------------------------------------
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
        GROUP BY
            t.teacher_id,
            t.first_name,
            t.last_name,
            c.class_id,
            c.class_name
        ORDER BY
            t.last_name,
            t.first_name,
            c.class_name;
    """)
    rows = cur.fetchall()

    # --------------------------------------------------
    # Query 2: Total unique students per teacher
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Build structured report for template rendering
    # --------------------------------------------------
    report = []
    current_tid = None
    teacher_block = None

    for r in rows:
        tid = r['teacher_id']

        # Start new teacher section
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

        # Add class info if class exists
        if r['class_id'] is not None:
            teacher_block['classes'].append({
                'class_name': r['class_name'],
                'student_count': r['student_count']
            })

    return render_template("teacher_report.html", report=report)




