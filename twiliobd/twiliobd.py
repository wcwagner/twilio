import click
import time
from collections import namedtuple
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, url_for
from werkzeug import check_password_hash, generate_password_hash
from icalendar import Calendar, Event

app = Flask('twiliobd')
app.config.from_envvar('CONFIGURATION_SETTINGS')
Birthday = namedtuple('Birthday', ['name', 'number', 'month', 'day', 'year'])

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """Initializes the database."""
    db = get_db() # open connection
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def _name(event):
    return str(event['summary']).replace("'s birthday", "")

def _birthdate(event):
    return event['DTSTART'].dt

@app.cli.command('populatedb')
@click.option('--path')
def loaddb(path):
    db = get_db()
    with app.open_resource('birthdays.ics', mode='r') as f:
        cal = Calendar.from_ical(f.read())
        birthday_generator = ( (_name(e), _birthdate(e))
                               for e in cal.walk('vevent') if e['summary'] )
        for name, birthdate in birthday_generator:
            insert_db('birthdays', fields=('name', 'birthdate'),
                      values=(name, birthdate))


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def insert_db(table, fields=(), values=()):
    db = get_db()
    cur = db.cursor()
    query = (f'INSERT INTO {table} ({", ".join(fields)})'
             f'VALUES ( { ",".join(["?"]*len(values))} )')
    cur.execute(query, values)
    db.commit()
    id = cur.lastrowid
    cur.close()
    return id



TEST_BIRTHDAYS = [
    Birthday('Foo Bar', '+17777777777', 10, 24, 1995),
    Birthday('Baz Foo', '+12222222222', 10, 24, 1996),
    Birthday('Bam Bar', '++13333333333', 10, 24, 1995),
    Birthday('Foo Baz', '++14444444444', 10, 25, 1995),
]

@app.route('/')
def index():
    print(app.config['TWILIO_ACCOUNT_SID'])
    return render_template('index.html', birthdays=TEST_BIRTHDAYS)

