import os
import sqlite3

from flask import Flask, g, render_template, request, redirect, abort

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(os.getenv('DB_PATH'))
    return db


@app.teardown_appcontext
def close_db_conn(_exc):
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()


@app.route('/')
def index():
    cur = get_db().execute('select id, title from notes where private = 0')
    cur.row_factory = lambda _, x: {'id': x[0], 'title': x[1]}
    notes = cur.fetchall()

    return render_template('index.html', notes=notes)


@app.route('/view/<int:note_id>')
def view_note(note_id: int):
    cur = get_db().execute(
        f'select title, content from notes where id = {note_id}')
    cur.row_factory = lambda _, x: {'title': x[0], 'content': x[1]}

    try:
        note = next(cur)
    except StopIteration:
        return abort(404)

    return render_template('view.html', note=note)


@app.route('/new', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            return abort(400)

        content = request.form.get('content')
        if not content:
            return abort(400)

        private = 1 if 'private' in request.form else 0

        cur = get_db().execute(
            f"insert into notes (private, title, content) values ('{private}', '{title}', '{content}')",
        )
        return redirect(f'/view/{cur.lastrowid}')

    return render_template('new.html')


def create_app():
    with app.app_context():
        get_db().execute("""
        create table if not exists notes (
            id integer primary key autoincrement, 
            private integer, 
            title text, 
            content text
        )""")

    return app


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
