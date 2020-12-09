import sqlite3
import random

import bcrypt
from flask import Flask, abort, redirect, render_template, request,session, url_for
from playhouse.shortcuts import model_to_dict
import peewee

from .models import modles, database, Companies, Categories, Movies, Users, MoviesCompany,  MoviesCategory, Reviews


app = Flask(__name__)
app.config.from_pyfile('config.py')


@app.before_request
def _db_connect():
    database.connect()


@app.teardown_request
def _db_close(_):
    if not database.is_closed():
        database.close()


app = Flask(__name__)
app.config.from_pyfile('config.py')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.j2')

    salt = bcrypt.gensalt(prefix=b'2b', rounds=10)
    unhashed_password = request.form['password'].encode('utf-8')
    hashed_password = bcrypt.hashpw(unhashed_password, salt)
    fields = {
        **request.form,
        'password': hashed_password,
        'level': 1,
    }
    user = Users(**fields)
    user.save()
    return 'Success!'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.j2')

    username = request.form['username']
    if username is None:
        return abort(400, 'No username supplied')

    try:
        user = Users.select().where(Users.username == username).get()
    except peewee.DoesNotExist:
        return abort(404, f'User {username} does not exists, please try again')

    password = request.form['password'].encode('utf-8')
    real_password = str(user.password).encode('utf-8')
    if not bcrypt.checkpw(password, real_password):
        return abort(403, 'Username and password does not match')

    session['username'] = user.username
    session['name'] = user.name
    session['id'] = user.id
    if session['username'] != 'admin':
        return render_template('rating.j2')
    return render_template('choose.j2')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    for session_value in ('username', 'name', 'level'):
        session.pop(session_value, None)
    return redirect(url_for('choose_login_register'))


@app.route('/<id_company>')
def company_produced_most_films(id_company):
    db = sqlite3.connect('manage_movies.db')
    cursor = db.cursor()
    query = Companies.select(Companies.name).where(Companies.id == id_company).limit(1).get()
    if query is None:
        return render_template('rating.j2', production_count='No such id')
    else:
        sentence = f"This id match {query.name} production"
        return render_template('rating.j2', production_count=sentence)
    

@app.route('/company_count', methods=['POST', 'GET'])
def company_count():
    if request.method == 'POST':
        comp_id = request.form['cn']
        if not comp_id:
            return render_template('company_movies_number.j2')
        return redirect(url_for('company_produced_most_films', id_company=comp_id))
    else:
        comp_id = request.args.get('cn')
        if not comp_id:
            return render_template('company_movies_number.j2')
        return redirect(url_for('company_produced_most_films', id_company=comp_id))


@app.route('/insert_category/<category>', methods=['POST', 'GET'])
def insert_category(category):
    b = True
    a = Categories.select(Categories.name).where(Categories.name == category)
    if not a.exists():
        id_company = random.randint(0,7000000)
        Categories.create(id=id_company, name=category)
        return 'Done'
    return 'Genre already exists'


@app.route('/insert', methods=['POST', 'GET'])
def insert():
    if request.method == 'POST':
        category_select = request.form['in']
        if not category_select:
            return render_template('categories_insert.j2')
        return redirect(url_for('insert_category', category=category_select))
    else:
        category_select = request.args.get('in')
        if not category_select:
            return render_template('categories_insert.j2')
        return redirect(url_for('insert_category', category=category_select))


@app.route('/delete_category/<category>', methods=['POST', 'GET'])
def delete_category(category):
    query = Categories.select(Categories.name).where(Categories.name == category)
    if query.exists():
        get_save_id = Categories.select(Categories.id).where(Categories.name == category)
        Categories.delete().where(Categories.name == category).execute()
        MoviesCategory.delete().where(MoviesCategory.movie_id == get_save_id).execute()
        return 'DONE'
    return f"Genre doesn't exists"


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    if request.method == 'POST':
        category_select = request.form['dl']
        if not category_select:
            return render_template('categories_delete.j2')
        return redirect(url_for('delete_category', category=category_select))
    else:
        category_select = request.args.get('fn')
        if not category_select:
            return render_template('categories_delete.j2')
        return redirect(url_for('delete_category', category=category_select))



@app.route('/vote/<id_movie>/<user_review>/<vote>', methods=['POST', 'GET'])
def update_vote_average_count(id_movie, user_review, vote):
    vote = float(vote)
    get_vote = Movies.select(Movies.vote_average).where(Movies.id == id_movie).limit(1).get()
    get_average = Movies.select(Movies.vote_count).where(Movies.id == id_movie).limit(1).get()
    new_vote = ((get_vote.vote_average * get_average.vote_count) + 1) / (get_average.vote_count + 1)
    updating_vote = Movies.update(vote_average = new_vote).where(Movies.id == id_movie)
    updating_vote.execute()
    updating_count = Movies.update(vote_count = get_average.vote_count + 1).where(Movies.id == id_movie).execute()
    Reviews.create(review=user_review, score=vote, user_id=session['id'], movie_id=id_movie)
    return 'Done'


@app.route('/rating', methods=['POST', 'GET'])
def rating():
    if request.method == 'POST':
        movie_idd = request.form['fn']
        movie_review = request.form['rv']
        movie_score = request.form['sc']
        if not movie_idd or not movie_review or not movie_score:
            return render_template('rating.j2')
        return redirect(url_for('update_vote_average_count', id_movie=movie_idd, user_review=movie_review, vote=movie_score))
    else:
        movie_idd = request.args.get('fn')
        movie_review = request.args.get('rv')
        movie_score = request.args.get('sc')
        if not movie_idd or not movie_review or not movie_score:
            return render_template('rating.j2')
        return redirect(url_for('update_vote_average_count', id_movie=movie_idd, user_review=movie_review, vote=movie_score))



@app.route('/choose', methods=['POST', 'GET'])
def choose():
    if request.method == 'POST':
        choose_action = request.form['ch']
        if choose_action == "d":
            return render_template('categories_delete.j2')
        elif choose_action == "i":
            return render_template('categories_insert.j2')
        else:
            return f'Only "d" and "i"' 
    else:
        choose_action = request.args.get('ch')
        if choose_action == "d":
            return render_template('categories_delete.j2')
        if choose_action == "i":
            return render_template('categories_insert.j2')

@app.route('/', methods=['POST', 'GET'])
def choose_login_register():
    if request.method == 'POST':
        choose_action = request.form['lr']
        if not choose_action:
            return render_template('choose_login_register.j2')
        if choose_action == "r":
            return render_template('register.j2')
        if choose_action == "l":
            return render_template('login.j2')
    else:
        choose_action = request.args.get('lr')
        if not choose_action:
            return render_template('choose_login_register.j2')
        if choose_action == "r":
            return render_template('register.j2')
        if choose_action == "l":
            return render_template('login.j2')


if __name__ == '__main__':
    app.run(threaded=True)
