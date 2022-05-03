from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DATABASE = "C:/Users/18016/OneDrive - Wellington College/Smile/smile.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "banana"

# Validation Function
   # - Checks names at least 2 characters
   # - checks for no incorrect characters

# cant access login or signup if logged in

# if we have a validation error, can we repopulate the form to save the user retyping

# welcome 'name' on menu page


def create_connection(db_file):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection to the file
    """
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    """
    A function to return whether the user is logged in or not
    """
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/menu')
def render_menu_page():
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, price, image, id FROM product"
    cur = con.cursor()  # Create cursor to run the query
    cur.execute(query)  # Runs the query
    product_list = cur.fetchall()
    con.close()

    if is_logged_in():
        fname = session['fname']
    else:
        fname = ""
    return render_template('menu.html', products=product_list, logged_in=is_logged_in(), user_id=fname)


@app.route('/addtocart/<product_id>')
def render_addtocart_page(product_id):
    try:
        product_id = int(product_id)
    except ValueError:
        print("{} is not an integer".format(product_id))
        return redirect("/menu?error=Invalid+product+id")

    userid = session['customer_id']
    timestamp = datetime.now()
    print("Add {} to cart".format(product_id))

    query = "INSERT INTO cart (customerid, productid, timestamp) VALUES (?, ?, ?)"
    con = create_connection(DATABASE)
    cur = con.cursor()

    # try to insert - this will fail if there is a foreign key
    try:
        cur.execute(query, (userid, product_id, timestamp))
    except sqlite3.IntegrityError as e:
        print(e)
        print("### PROBLEM INSERTING INTO DATABASE - FOREIGN KEY ###")
        con.close()
        return redirect('/menu?error=Something+went+very+very+wrong')

    con.commit()
    con.close()
    return redirect(request.referrer)


@app.route('/cart')
def render_cart_page():
    if not is_logged_in():
        return redirect('/menu')
    else:
        customer_id = session['customer_id']
        query = "SELECT productid FROM cart WHERE customerid=?;"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (customer_id,))
        product_ids = cur.fetchall()
        print(product_ids)

        for i in range(len(product_ids)):
            product_ids[i] = product_ids[i][0]
        print(product_ids)

        unique_product_ids = list(set(product_ids))
        print(unique_product_ids)

        for i in range(len(unique_product_ids)):
            product_count = product_ids.count(unique_product_ids[i])
            unique_product_ids[i] = [unique_product_ids[i], product_count]
        print(unique_product_ids)
        total = 0
        query = "SELECT name, price FROM product WHERE id = ?"
        for item in unique_product_ids:
            cur.execute(query, (item[0], ))
            item_details = cur.fetchall()
            print(item_details)
            item.append(item_details[0][0])
            item.append(item_details[0][1])
            item.append(item[1] * item[3])
            print(item)
            total += item[4]
        con.close()
        return render_template('cart.html', cart_data=unique_product_ids, logged_in=is_logged_in(), total=total, fname=session['fname'])


@app.route('/removeonefromcart/<product_id>')
def remove_one(product_id):
    if is_logged_in():
        customer_id = session['customer_id']
        query = "DELETE FROM cart WHERE id = (SELECT min(id) FROM cart WHERE customerid = ? AND productid = ?)"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (customer_id, product_id))
        con.commit()
        con.close()
    return redirect("/cart")


@app.route('/confirmorder')
def confirmorder():
    userid = session['userid']
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "DELETE FROM cart WHERE userid=?;"
    cur.execute(query, (userid,))
    con.commit()
    con.close()
    return redirect('/?message=Order+complete')


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in=is_logged_in())


@app.route('/login', methods=['Get', 'Post'])
def render_login_page():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, fname, password FROM customer WHERE email=? "
        cur = con.cursor()
        cur.execute(query, (email, ))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]

        else:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")
        # Set up a session for the login to tell the program I'm logged in
        session['email'] = email
        session['customer_id'] = user_id
        session['fname'] = first_name
        session['cart'] = []
        return redirect('/menu')

    return render_template('login.html', logged_in=is_logged_in())


@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?messsage=See=you+next+time')


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
            return redirect('/signup?error=Password+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)

        query = "INSERT INTO customer (fname, lname, email, password) VALUES(?, ?, ?, ?)"

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()
        return redirect('/login')  # takes user back to the login page

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in())


app.run(host='0.0.0.0', debug=True)
