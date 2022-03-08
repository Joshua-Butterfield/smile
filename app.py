from flask import Flask, render_template, request, redirect
import sqlite3
from sqlite3 import Error

DATABASE = "C:/Users/18016/OneDrive - Wellington College/Smile/smile.db"
app = Flask(__name__)


def create_connection(db_file):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection to the file
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None



@app.route('/')
def render_homepage():
    return render_template('home.html')


@app.route('/menu')
def render_menu_page():
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, price, image FROM product"
    cur = con.cursor()  # Create cursor to run the query
    cur.execute(query)  # Runs the query
    product_list = cur.fetchall()
    print(product_list)
    con.close()
    return render_template('menu.html', products=product_list)


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html')


@app.route('/login', methods=['Get', 'Post'])
def render_login_page():
    return render_template('login.html')


@app.route('/signup', methods=['Get', 'Post'])
def render_signup_page():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Check to see whether the passwords match
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+at+least+8+character')


        con = create_connection(DATABASE)

        query = "INSERT INTO customer (fname, lname, email, password) VALUES(?, ?, ?, ?)"

        cur = con.cursor()
        cur.execute(query, (fname, lname, email, password))
        con.commit()
        con.close()
        return redirect('/login')  #takes user back to the login page

    return render_template('signup.html')


app.run(host='0.0.0.0', debug=True)
