# -*- coding: utf-8 -*-
"""
	schall und rauch
	based on Flaskr
	:copyright: (c) 2010 by Armin Ronacher, 2013 by zakx <sg@unkreativ.org>
	:license: BSD, see LICENSE for more details.
"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
	 render_template, flash
from werkzeug.routing import BaseConverter
import re
import datetime

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
	DATABASE='/tmp/flaskr.db',
	DEBUG=True,
	SECRET_KEY='development key',
	USERNAME='admin',
	PASSWORD='foo'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

class RegexConverter(BaseConverter):
	def __init__(self, url_map, *items):
		super(RegexConverter, self).__init__(url_map)
		self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

def connect_db():
	"""Connects to the specific database."""
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv


def init_db():
	"""Creates the database tables."""
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()


def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
	"""Closes the database again at the end of the request."""
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()


@app.route('/')
def show_entries():
	db = get_db()
	cur = db.execute('select distinct date from entries order by date desc')
	entries = cur.fetchall()
	return render_template('show_entries.html', entries=entries, day=datetime.date.today(), time=datetime.datetime.now().strftime("%H:%M"))

@app.route('/<regex("(\d){4}-(\d){2}-(\d){2}"):date>/')
def show_day(date):
	db = get_db()
	cur = db.execute('select * from entries where date = ? order by time desc',
					[date,])
	entries = cur.fetchall()
	return render_template('show_day.html', entries=entries, day=date, time=datetime.datetime.now().strftime("%H:%M"))

@app.route('/<regex("(\d){4}-(\d){2}-(\d){2}"):date>/delete/', methods=['GET'])
def delete_post(date):
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	db.execute('delete from entries where id = ?', [int(request.args['id']),])
	db.commit()
	flash('Entry was successfully deleted')
	return redirect(url_for('show_day', date=date))

@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	if not re.match(r'^(\d){4}-(\d){2}-(\d){2}$', request.form['date']):
		flash('Not a valid date.')
		return redirect(url_for('show_entries'))
	if not re.match(r'^(\d){2}:(\d){2}$', request.form['time']):
		flash('Not a valid time.')
		return redirect(url_for('show_entries'))
	db = get_db()
	db.execute('insert into entries (date, time, text) values (?, ?, ?)',
				 [request.form['date'], request.form['time'], request.form['text'],])
	db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_day', date=request.form['date']))


@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)


@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))


if __name__ == '__main__':
	#init_db()
	app.run()
