from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateTimeLocalField, SubmitField, PasswordField, DecimalField, TimeField, \
    DateField
from wtforms.validators import Length, NumberRange, InputRequired, Optional, ValidationError

rus_length = Length(min=1, max=45, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_number_range = NumberRange(min=1, max=99999999999, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_input_required = InputRequired(message='Заполните поле')
rus_price_range = NumberRange(min=1, max=10000, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_percent_range = NumberRange(min=1, max=100, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')


def date_check(form, field):
    if field.data < datetime.today():
        raise ValidationError('Введите не прошедшую дату')


class LoginForm(FlaskForm):
    login = StringField('Логин', [rus_input_required, rus_length])
    password = PasswordField('Пароль', [rus_input_required, rus_length])
    submit = SubmitField('Войти')


class UserForm(FlaskForm):
    username = StringField('Имя пользователя', [rus_input_required, rus_length])
    password = PasswordField('Пароль', [rus_input_required, rus_length])
    fio = StringField('ФИО', [rus_input_required, rus_length])
    document_id = SelectField('Тип документа', [rus_input_required])
    document_number = DecimalField('Номер документа', [rus_input_required])
    role = SelectField('Роль', [rus_input_required])
    submit = SubmitField('Добавить')


class AircraftForm(FlaskForm):
    name = StringField('Название', [rus_input_required, rus_length])
    capacity = DecimalField('Вместимость', [rus_input_required, rus_number_range])
    plate = DecimalField('Номер', [rus_input_required, rus_number_range])
    submit = SubmitField('Добавить')


class AirportForm(FlaskForm):
    name = StringField('Название', [rus_input_required, rus_length])
    city = StringField('Город', [rus_input_required, rus_length])
    address = StringField('Адрес', [rus_input_required, rus_length])
    submit = SubmitField('Добавить')


class RouteForm(FlaskForm):
    number = DecimalField('Номер маршрута', [rus_input_required, rus_price_range])
    a1 = SelectField('Аэропорт вылета', [rus_input_required])
    a2 = SelectField('Аэропорт назначения', [rus_input_required])
    price = DecimalField('Цена билета', [rus_input_required, rus_price_range])
    time = TimeField('Время в полете', [rus_input_required])
    submit = SubmitField('Добавить')


class FlightForm(FlaskForm):
    route = SelectField('Маршрут', [rus_input_required])
    aircraft = SelectField('Самолет', [rus_input_required])
    date = DateTimeLocalField('Дата отправления', format='%Y-%m-%dT%H:%M', validators=[rus_input_required, date_check])
    submit = SubmitField('Добавить')


class FilterFlightForm(FlaskForm):
    a1 = SelectField('Аэропорт вылета', [Optional()])
    a2 = SelectField('Аэропорт назначения', [Optional()])
    date2 = DateField('Дата вылета', format='%Y-%m-%d', validators=[Optional()])
    submit2 = SubmitField('Показать')
