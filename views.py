import hashlib
from datetime import datetime

from flask import url_for, render_template, request, redirect, send_from_directory, flash, session
from __init__ import app
import forms
from repo import *

repo = Repo(host=app.config['HOST'], user=app.config['USER'], password=app.config['PASSWORD'], db=app.config['DB'])


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error)


@app.route("/")
def index():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template('index.html', title="Главная")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get('loggedin'):
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = repo.login_user(form.login.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        if user:
            flash('Вы авторизовались!')
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[6]
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))


@app.route("/users", methods=['GET', 'POST'])
def users():
    form = forms.UserForm()
    form.role.choices = repo.get_roles()
    form.document_id.choices = repo.select_documents()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_user(form.username.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest(), form.fio.data, form.document_id.data, form.document_number.data, form.role.data):
                flash('Пользователь уже существует')
            else:
                app.logger.warning(f'User {form.username.data} with role id {form.role.data} was added by {session.get("username")}')
            return redirect(url_for('users'))
    return render_template('users.html', title='Пользователи', us=repo.get_all_users(), form=form)


@app.route("/users/rm/<int:id>")
def user_rm(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_user(id)
    return redirect(url_for('users'))


@app.route("/aircrafts", methods=['GET', 'POST'])
def aircrafts():
    form = forms.AircraftForm()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_aircraft_check(form.name.data, form.capacity.data, form.plate.data):
                flash('Введите уникальный номер')
            return redirect(url_for('aircrafts'))
    return render_template('aircrafts.html', title="Самолеты", ss=repo.get_aircrafts(), form=form)


@app.route("/aircrafts/rm/<int:id>")
def aircraft_rm(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_aircraft(id)
    return redirect(url_for("aircrafts"))


@app.route("/airports", methods=['GET', 'POST'])
def airports():
    form = forms.AirportForm()

    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_airport_check(form.name.data, form.city.data, form.address.data):
                flash('Введите уникальное название')
            return redirect(url_for('airports'))

    return render_template('airports.html', title="Аэропорты", airports=repo.get_airports(), form=form)


@app.route("/airports/rm/<int:id>")
def rm_airport(id):
    if session.get('role') >= repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_airport(id)
    return redirect(url_for("airports"))


@app.route("/routes", methods=['GET', 'POST'])
def routes():
    form = forms.RouteForm()
    form.a1.choices = repo.select_airports()
    form.a2.choices = repo.select_airports()
    if form.validate_on_submit() and session.get('role') == repo.ROLE_ADMINISTRATOR:
        if form.a1.data == form.a2.data:
            flash('Выберите разные аэропорты')
            return redirect(url_for("routes"))
        if not repo.add_route_check(form.number.data, form.a1.data, form.a2.data, form.price.data, form.time.data):
            flash('Введите уникальный номер маршрута')
        return redirect(url_for("routes"))
    return render_template('routes.html', title="Маршруты", routes=repo.get_routes(), form=form)


@app.route("/routes/rm/<int:id>")
def rm_route(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_route(id)
    return redirect(url_for("routes"))


@app.route("/flights", methods=["GET", "POST"])
def flights():
    form = forms.FlightForm()
    form.aircraft.choices = repo.select_aircrafts()
    form.route.choices = repo.select_routes()

    filter_form = forms.FilterFlightForm()
    filter_form.a1.choices = repo.select_airports()
    filter_form.a2.choices = repo.select_airports()

    if filter_form.validate_on_submit():
        return render_template('flights.html', title="Рейсы", flights=repo.get_flights_sorted(filter_form.a1.data, filter_form.a2.data, filter_form.date2.data), form=form, filter_form=filter_form)

    return render_template('flights.html', title="Рейсы", flights=repo.get_flights(), form=form, filter_form=filter_form)


@app.route('/flights/add', methods=['POST'])
def add_flight():
    form = forms.FlightForm()
    form.aircraft.choices = repo.select_aircrafts()
    form.route.choices = repo.select_routes()
    if form.validate_on_submit() and session.get('role') >= repo.ROLE_DISPATCHER:
        if repo.add_flight_with_check(form.route.data, form.aircraft.data, form.date.data):
            app.logger.warning(f'New flight added by {session.get("username")}')
        else:
            flash('В это время самолет уже занят')
    else:
        flash_errors(form)
    return redirect(url_for("flights"))


@app.route("/flights/buy/<int:id>")
def buy_ticket(id):
    if len(repo.get_seat_by_user_and_flight(id, session.get('id'))) == 0:
        if not repo.buy_ticket(id, session.get('id'), datetime.today()):
            flash("Все места заняты")
        else:
            flash('Билет куплен')
    else:
        flash('Вы уже купили билет на данный рейс')
    return redirect(url_for("flights"))


@app.route("/flights/<int:id>", methods=["GET", "POST"])
def flight(id):
    if session.get('role') > repo.ROLE_PASSENGER:
        print(repo.get_seats_of_flight(id))
        return render_template('flight.html', title="Рейс", c=repo.get_flight(id)[0], passengers=repo.get_seats_of_flight(id))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('contracts'))


@app.route("/flights/rm/<int:id>")
def flights_remove(id):
    if session.get('role') >= repo.ROLE_DISPATCHER:
        if not repo.remove_flight(id):
            flash('Что-то не так')
            return redirect(url_for("flight", id=id))
    flash('Рейс отменен')
    return redirect(url_for("flight"))


@app.route('/tickets')
def tickets():
    return render_template('tickets.html', title='Ваши билеты', tickets=repo.get_seats_of_user(session.get('id')))


@app.route('/tickets/rm/<int:id>')
def rm_ticket(id):
    repo.rm_seat(id, session.get('id'))
    return redirect(url_for('tickets'))


@app.route('/profit')
def profit():
    return repo.get_profit_by_month()


@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
@app.route('/style.css')
@app.route('/script.js')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
