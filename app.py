from flask import Flask, render_template
import sqlite3
from sqlite3 import error

DATABASE = Tutoring_db

app = Flask(__name__)


@app.route('/')
def render_homepage():
    """

    :param: none
    :return: home page template
    """
    return render_template('home.html')


if __name__ == '__main__':
    app.run()
