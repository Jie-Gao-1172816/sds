from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
import db
import connect
from datetime import datetime


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
    # Add your code here to list customers
    return render_template("student_list.html")


# Add other routes and view functions as required.

