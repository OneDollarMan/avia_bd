import hashlib
from datetime import datetime

from flask import url_for, render_template, request, redirect, send_from_directory, flash, session
from __init__ import app
import forms
from repo import *

repo = Repo(host=app.config['HOST'], user=app.config['USER'], password=app.config['PASSWORD'], db=app.config['DB'])


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
            session['role'] = user[4]
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
            redirect(url_for('users'))
    return render_template('users.html', title='Работники', us=repo.get_all_users(), form=form)


@app.route("/users/rm/<int:id>")
def user_rm(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.rm_user(id)
    return redirect(url_for('users'))


@app.route("/aircrafts", methods=['GET', 'POST'])
def aircrafts():
    form = forms.AircraftForm()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            repo.add_aircraft(form.name.data, form.capacity.data, form.plate.data)
            return redirect(url_for('aircrafts'))
    return render_template('aircrafts.html', title="Самолеты", ss=repo.get_aircrafts(), form=form)


@app.route("/suppliers/<int:supplierid>")
def supplier(supplierid):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        return render_template('supplier.html', title="Поставщик", s=repo.get_supplier(supplierid),
                               ps=repo.get_food_of_supplier(supplierid))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('suppliers'))


@app.route("/suppliers/rm/<int:id>")
def suppliers_rm(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.rm_supplier(id)
    return redirect(url_for("suppliers"))


@app.route("/airports", methods=['GET', 'POST'])
def airports():
    form = forms.AirportForm()

    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            repo.add_airport(form.name.data, form.city.data, form.address.data)
            return redirect(url_for('airports'))

    return render_template('airports.html', title="Аэропорты", airports=repo.get_airports(), form=form)


@app.route("/food/<int:id>")
def food(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        return render_template('food.html', title="Продукт", p=repo.get_food(id), cs=repo.get_contracts_of_food(id))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('foods'))


@app.route("/food/rm/<int:id>")
def food_remove(id):
    if session.get('role') >= repo.ROLE_STOREKEEPER:
        if id:
            repo.rm_food(id)
    return redirect(url_for("food"))


@app.route("/routes", methods=['GET', 'POST'])
def routes():
    form = forms.RouteForm()
    form.a1.choices = repo.select_airports()
    form.a2.choices = repo.select_airports()
    if form.validate_on_submit() and session.get('role') == repo.ROLE_ADMINISTRATOR:
        repo.add_route(form.number.data, form.a1.data, form.a2.data, form.price.data, form.time.data)
        redirect(url_for("routes"))
    return render_template('routes.html', title="Маршруты", routes=repo.get_routes(), form=form)


@app.route("/customers/<int:id>")
def customer(id):
    c = repo.get_customer(id)
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        return render_template('customer.html', title="Заказчик", c=c, ss=repo.get_contracts_of_customer(id))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('customers'))


@app.route("/customers/rm/<int:id>")
def customers_remove(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.rm_customer(id)
    return redirect(url_for("customers"))


@app.route("/flights", methods=["GET", "POST"])
def flights():
    form = forms.FlightForm()
    form.aircraft.choices = repo.select_aircrafts()
    form.route.choices = repo.select_routes()

    if form.validate_on_submit() and session.get('role') == repo.ROLE_ADMINISTRATOR:
        repo.add_flight(form.route.data, form.aircraft.data, form.date.data)
        app.logger.warning(f'New flight added by {session.get("username")}')
        return redirect(url_for("flights"))

    return render_template('flights.html', title="Рейсы", flights=repo.get_flights(), form=form)


@app.route("/flights/buy/<int:id>")
def buy_ticket(id):
    if len(repo.get_seat_by_user_and_flight(id, session.get('id'))) == 0:
        if not repo.buy_ticket(id, session.get('id'), datetime.today()):
            flash("Все места заняты")
    else:
        flash('Вы уже купили билет на данный рейс')
    return redirect(url_for("flights"))


@app.route("/contracts/add", methods=['POST'])
def add_contract():
    contract_form = forms.ContractForm()
    contract_form.customer.choices = repo.select_customers()

    if contract_form.validate_on_submit():
        if session.get('role') >= repo.ROLE_STOREKEEPER:
            repo.add_contract(d=contract_form.date.data, c=contract_form.customer.data, p=contract_form.percent.data)
    return redirect(url_for("contracts"))


@app.route("/flights/<int:id>", methods=["GET", "POST"])
def flight(id):
    if session.get('role') >= repo.ROLE_PASSENGER:
        return render_template('flight.html', title="Рейс", c=repo.get_flight(id))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('contracts'))


@app.route('/contracts/<int:id>/status', methods=['POST'])
def status(id):
    status_form = forms.StatusForm()
    status_form.status.choices = repo.select_statuses()
    if status_form.validate_on_submit():
        repo.change_contract_status(id, status_form.status.data)
        flash('Статус изменен')
    return redirect(url_for("contract", id=id))


@app.route("/contracts/<int:cid>/rm_food/<int:fid>", methods=['GET'])
def contracts_remove_food(cid, fid):
    if session.get('role') >= repo.ROLE_STOREKEEPER:
        if cid and fid:
            repo.remove_food_from_contract(cid, fid)
            flash('Позиция удалена')
    return redirect(url_for("contract", id=cid))


@app.route("/contracts/rm/<int:id>")
def contracts_remove(id):
    if session.get('role') >= repo.ROLE_STOREKEEPER:
        if not repo.remove_contract(id):
            flash('Сначала очистите список продуктов')
            return redirect(url_for("contract", id=id))
    flash('Контракт удален')
    return redirect(url_for("contracts"))


@app.route('/tickets')
def tickets():
    return render_template('tickets.html', title='Ваши билеты', tickets=repo.get_seats_of_user(session.get('id')))


@app.route('/tickets/rm/<int:id>')
def rm_ticket(id):
    repo.rm_seat(id, session.get('id'))
    return redirect(url_for('tickets'))


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
