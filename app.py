from flask import Flask, render_template, request, redirect
import db, connect

app = Flask(__name__)
connection = db.init_db(app, user=connect.dbuser, password=connect.dbpass, host=connect.dbhost,database=connect.dbname, port=connect.dbport, autocommit=True)


@app.route('/')
def index():
    cur = db.get_cursor()
    cur.execute("SELECT * from people;")
    results = cur.fetchall()
    #print(results)
    #for row in results:
     #   print(f" {row['name']} is ID {row['id']} \n")
   # return "Check console for database query results."
    cur.close()
    return render_template('results.html', people=results)

@app.route('/details')
def details():
    #print(request.args)
    id = request.args.get('id')
    cur = db.get_cursor()
    cur.execute("SELECT * from people where id = %s;", (id,))
    result = cur.fetchone()
    print(result)
    cur.close()
    return render_template('details.html', person=result)

@app.route('/details/update', methods=['POST'])
def update_details():
    print(request.form)
    id = request.form.get('id')
    name = request.form.get('name')
    city = request.form.get('city')
    sex = request.form.get('sex')
    age = request.form.get('age')
    weight = request.form.get('weight')

# UPDATE table_name
# SET column1 = value1, column2 = value2, ...
# WHERE condition;
    cur = db.get_cursor()
    cur.execute("UPDATE people SET name = %s, city = %s, sex = %s, age = %s, weight = %s WHERE id = %s;", (name, city, sex, age, weight, id))
    cur.close()
    #result = {'name': "Edited Name", 'city': "Edited City"}
    return redirect(f'/details?id={id}')