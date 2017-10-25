import click
import time
from collections import namedtuple
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, url_for, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
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
    """ Extracts name from Facebook birthday events export """
    return str(event['summary']).replace("'s birthday", "")

def _birthdate(event):
    """ Extracts birthdate from Facebook birthday events export """
    return event['DTSTART'].dt

@app.cli.command('populatedb')
@click.option('--path')
def loaddb(path):
    """Populates database with birthdays from Facebook birthday events export"""
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
    """Inserts into the database and returns id of last row inserted"""
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
    return render_template('index.html', birthdays=TEST_BIRTHDAYS)


@app.route('/text', methods=['POST'])
def text():
    """Endpoint to send happy birthday text via Twilio API"""
    phone_number = request.form.get('phoneNumber', None)
    name = request.form.get('name', None)
    try:
        twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'],
                               app.config['TWILIO_AUTH_TOKEN'])
    except Exception as e:
        msg = 'Missing configuration variable: {0}'.format(e)
        return jsonify({'error': msg})

    try:
        twilio_client.messages.create(from_=app.config['TWILIO_CALLER_ID'],
                                   to='+17723416961', # default to my number for now
                                   body=f'Happy Birthday {name}!')
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': str(e)})

    return jsonify({'message': 'Text incoming!'})


@app.route('/call', methods=['POST'])
def call():
    """Endpoint to send happy birthday call via Twilio API"""
    phone_number = request.form.get('phoneNumber', None)
    name = request.form.get('name', None)
    try:
        twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'],
                               app.config['TWILIO_AUTH_TOKEN'])
    except Exception as e:
        msg = 'Missing configuration variable: {0}'.format(e)
        return jsonify({'error': msg})

    try:
        twilio_client.calls.create(from_=app.config['TWILIO_CALLER_ID'],
                                   to=app.config['MY_NUMBER'],
                                   url=url_for('.outbound',
                                               _external=True,
                                               name=name))
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': str(e)})

    return jsonify({'message': 'Call incoming!'})


@app.route('/outbound', methods=['POST'])
def outbound():
    response = VoiceResponse()
    name = request.form.get('name', None)
    response.say(f'Happy birthday {name}!', voice='man')
    return str(response)

