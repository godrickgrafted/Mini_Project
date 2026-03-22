from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "tutoring_DB"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "asdgfjklj"


def is_logged_in():
    """
    Checks whether the user is logged in.

    :param: none
    :return: True if user is logged in, otherwise False
    """
    if session.get('user_id') is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


def connect_database(db_file):
    """
    Creates a connection with the database.

    :param db_file: the name of the database file
    :return: database connection
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print("An error occurred when connecting to the database.")
    return


@app.route('/')
def render_homepage():
    """
    Renders the home page.

    :param: none
    :return: home.html
    """
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup_page():
    """
    Allows a new user to sign up.

    :param: none
    :return: signup.html or redirect to login
    """
    if request.method == 'POST':
        fname = request.form.get('user_fname').title().strip()
        lname = request.form.get('user_lname').title().strip()
        email = request.form.get('user_email').lower().strip()
        password = request.form.get('user_password')
        password2 = request.form.get('user_password2')
        role = request.form.get('user_role')

        if password != password2:
            return redirect('/signup')

        if len(password) < 8:
            return redirect('/signup')

        hashed_password = bcrypt.generate_password_hash(password)

        con = connect_database(DATABASE)
        cur = con.cursor()

        query_check = "SELECT * FROM user WHERE email = ?"
        cur.execute(query_check, (email,))
        existing_user = cur.fetchone()

        if existing_user is not None:
            con.close()
            return redirect('/signup')

        query_insert = """
            INSERT INTO user (first_name, last_name, email, password, role)
            VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(query_insert, (fname, lname, email, hashed_password, role))
        con.commit()
        con.close()

        return redirect('/login')

    return render_template('signup.html', logged_in=is_logged_in())


@app.route('/login', methods=['POST', 'GET'])
def render_login_page():
    """
    Logs a user into the website.

    :param: none
    :return: login.html or redirect to home
    """
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        email = request.form['user_email'].strip().lower()
        password = request.form['user_password']

        query = "SELECT user_id, first_name, last_name, email, password, role FROM user WHERE email = ?"
        con = connect_database(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_info = cur.fetchone()
        cur.close()
        con.close()

        try:
            user_id = user_info[0]
            first_name = user_info[1]
            last_name = user_info[2]
            user_email = user_info[3]
            user_password = user_info[4]
            role = user_info[5]
        except TypeError:
            return redirect('/login')

        if not bcrypt.check_password_hash(user_password, password):
            return redirect('/login')

        session['email'] = user_email
        session['user_id'] = user_id
        session['first_name'] = first_name
        session['last_name'] = last_name
        session['role'] = role

        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in())


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    Logs the current user out.

    :param: none
    :return: redirect to home page
    """
    session.clear()
    return redirect('/')


@app.route('/sessions')
def render_sessions_page():
    """
    Renders the page showing all tutoring sessions.

    :param: none
    :return: sessions.html
    """
    con = connect_database(DATABASE)
    cur = con.cursor()

    query = """
        SELECT sessions.session_id,
               sessions.title,
               sessions.description,
               sessions.session_date,
               sessions.session_time,
               sessions.location,
               subjects.subject_name,
               tutor.first_name || ' ' || tutor.last_name AS tutor_name,
               creator.first_name || ' ' || creator.last_name AS creator_name
        FROM sessions
        JOIN subjects ON sessions.fk_subject_id = subjects.subject_id
        JOIN user AS tutor ON sessions.fk_tutor_id = tutor.user_id
        JOIN user AS creator ON sessions.fk_creator_id = creator.user_id
        ORDER BY sessions.session_date, sessions.session_time
    """

    cur.execute(query)
    session_list = cur.fetchall()
    con.close()

    return render_template(
        'sessions.html',
        list_of_sessions=session_list,
        logged_in=is_logged_in()
    )


@app.route('/create_session', methods=['POST', 'GET'])
def render_create_session_page():
    """
    Allows tutors to create tutoring sessions.

    :param: none
    :return: create_session.html
    """
    if not is_logged_in():
        return redirect('/login')

    if session.get('role') != 'tutor':
        return redirect('/sessions')

    con = connect_database(DATABASE)
    cur = con.cursor()

    query_subjects = "SELECT * FROM subjects"
    cur.execute(query_subjects)
    subject_list = cur.fetchall()

    if request.method == 'POST':
        title = request.form.get('title').strip()
        description = request.form.get('description').strip()
        session_date = request.form.get('session_date')
        session_time = request.form.get('session_time')
        location = request.form.get('location').strip()
        fk_subject_id = request.form.get('subject_id')

        query_insert = """
            INSERT INTO sessions
            (title, description, session_date, session_time, location, fk_subject_id, fk_creator_id, fk_tutor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        cur.execute(query_insert, (
            title,
            description,
            session_date,
            session_time,
            location,
            fk_subject_id,
            session['user_id'],
            session['user_id']
        ))

        con.commit()
        con.close()

        return redirect('/sessions')

    con.close()
    return render_template(
        'create_session.html',
        list_of_subjects=subject_list,
        logged_in=is_logged_in()
    )


if __name__ == "__main__":
    app.run()