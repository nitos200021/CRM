import os

project_structure = {
    'project': {
        'app.py': """from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from models import db, Ticket, Employee, House, WorkType, User
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class TicketForm(FlaskForm):
    ticket_number = StringField('Номер заявки', validators=[DataRequired()])
    description = TextAreaField('Описание проблемы', validators=[DataRequired()])
    address = SelectField('Адрес проблемы', coerce=int, validators=[DataRequired()])
    criticality = SelectField('Критичность заявки', choices=[('Низкая','Низкая'),('Средняя','Средняя'),('Высокая','Высокая')], validators=[DataRequired()])
    contact_name = StringField('ФИО', validators=[DataRequired()])
    contact_phone = StringField('Телефон', validators=[DataRequired()])
    work_type = SelectField('Тип работ', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Создать заявку')

class EditTicketForm(FlaskForm):
    status = SelectField('Статус заявки', choices=[('Новая','Новая'),('В работе','В работе'),('Выполнена','Выполнена'),('Отменена','Отменена')], validators=[DataRequired()])
    start_time = DateTimeField('Время начала работы (ГГГГ-ММ-ДД ЧЧ:ММ)', format='%Y-%m-%d %H:%M', default=datetime.utcnow)
    end_time = DateTimeField('Время окончания работы (ГГГГ-ММ-ДД ЧЧ:ММ)', format='%Y-%m-%d %H:%M')
    assigned_employee = SelectField('Исполнитель', coerce=int, validators=[DataRequired()])
    responsible_person = StringField('Ответственный (мастер смены)', validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def seed_data():
    if not House.query.first():
        houses = [House(address='ул. Ленина, д. 1'),House(address='ул. Ленина, д. 2'),House(address='пр. Мира, д. 10')]
        db.session.add_all(houses)
    if not WorkType.query.first():
        works = [WorkType(name='Электрика', description='Работы по электрике'),WorkType(name='Сантехника', description='Работы по сантехнике'),WorkType(name='Отделка', description='Косметический ремонт')]
        db.session.add_all(works)
    if not Employee.query.first():
        employees = [Employee(name='Иван Иванов', position='Мастер'),Employee(name='Пётр Петров', position='Специалист'),Employee(name='Сергей Сергеев', position='Инженер')]
        db.session.add_all(employees)
    if not User.query.first():
        user = User(username='admin', password='admin')
        db.session.add(user)
    db.session.commit()

@app.before_first_request
def initialize():
    db.create_all()
    seed_data()

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль','danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    ticket_query = Ticket.query
    date_filter = request.args.get('date')
    work_filter = request.args.get('work')
    address_filter = request.args.get('address')
    criticality_filter = request.args.get('criticality')
    employee_filter = request.args.get('employee')
    responsible_filter = request.args.get('responsible')
    status_filter = request.args.get('status')
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
            ticket_query = ticket_query.filter(db.func.date(Ticket.created_at)==date_obj.date())
        except Exception:
            flash('Неверный формат даты. Используйте ГГГГ-ММ-ДД.','danger')
    if work_filter:
        ticket_query = ticket_query.join(WorkType).filter(WorkType.id==int(work_filter))
    if address_filter:
        house = House.query.get(int(address_filter))
        if house:
            ticket_query = ticket_query.filter(Ticket.address==house.address)
    if criticality_filter:
        ticket_query = ticket_query.filter(Ticket.criticality==criticality_filter)
    if employee_filter:
        ticket_query = ticket_query.filter(Ticket.assigned_employee_id==int(employee_filter))
    if responsible_filter:
        ticket_query = ticket_query.filter(Ticket.responsible_person==responsible_filter)
    if status_filter:
        ticket_query = ticket_query.filter(Ticket.status==status_filter)
    tickets = ticket_query.order_by(Ticket.created_at.desc()).all()
    houses = House.query.all()
    work_types = WorkType.query.all()
    employees = Employee.query.all()
    return render_template('index.html', tickets=tickets, houses=houses, work_types=work_types, employees=employees)

@app.route('/ticket/new', methods=['GET','POST'])
@login_required
def create_ticket():
    houses = House.query.filter_by(active=True).all()
    work_types = WorkType.query.all()
    form = TicketForm()
    form.address.choices = [(house.id, house.address) for house in houses]
    form.work_type.choices = [(wt.id, wt.name) for wt in work_types]
    if form.validate_on_submit():
        selected_house = House.query.get(form.address.data)
        selected_work = WorkType.query.get(form.work_type.data)
        new_ticket = Ticket(ticket_number=form.ticket_number.data,description=form.description.data,address=selected_house.address,criticality=form.criticality.data,contact_name=form.contact_name.data,contact_phone=form.contact_phone.data,work_type=selected_work)
        db.session.add(new_ticket)
        db.session.commit()
        flash('Заявка успешно создана.','success')
        return redirect(url_for('index'))
    return render_template('create_ticket.html', form=form)

@app.route('/ticket/<int:ticket_id>/edit', methods=['GET','POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    employees = Employee.query.all()
    form = EditTicketForm(obj=ticket)
    form.assigned_employee.choices = [(emp.id, f'{emp.name} - {emp.position}') for emp in employees]
    if ticket.assigned_employee_id:
        form.assigned_employee.data = ticket.assigned_employee_id
    if form.validate_on_submit():
        ticket.status = form.status.data
        ticket.start_time = form.start_time.data
        ticket.end_time = form.end_time.data
        ticket.assigned_employee_id = form.assigned_employee.data
        ticket.responsible_person = form.responsible_person.data
        db.session.commit()
        flash('Заявка успешно обновлена.','success')
        return redirect(url_for('index'))
    return render_template('edit_ticket.html', form=form, ticket=ticket)

@app.route('/act/<int:ticket_id>')
@login_required
def act(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('act.html', ticket=ticket)

@app.route('/reset', methods=['GET','POST'])
@login_required
def reset():
    if request.method == 'POST':
        try:
            db.session.query(Ticket).delete()
            db.session.query(Employee).delete()
            db.session.query(House).delete()
            db.session.query(WorkType).delete()
            db.session.commit()
            flash('Вся информация успешно удалена.','warning')
        except Exception:
            db.session.rollback()
            flash('Ошибка при удалении данных.','danger')
        return redirect(url_for('index'))
    return render_template('reset.html')

if __name__ == '__main__':
    app.run(debug=True)
""",
        'config.py': """class Config:
    SECRET_KEY = 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://wr8:251312nikNIK*@localhost/work?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
""",
        'models.py': """from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
db = SQLAlchemy()
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
class WorkType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    criticality = db.Column(db.String(50), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(50), nullable=False)
    work_type_id = db.Column(db.Integer, db.ForeignKey('work_type.id'), nullable=True)
    status = db.Column(db.String(50), default='Новая')
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    responsible_person = db.Column(db.String(100), nullable=True)
    work_type = db.relationship('WorkType', backref=db.backref('tickets', lazy=True))
    assigned_employee = db.relationship('Employee', backref=db.backref('tickets', lazy=True))
""",
        'requirements.txt': """Flask==2.2.5
Flask-SQLAlchemy==3.0.5
Flask-WTF==1.1.1
pymysql==1.0.3
WTForms==3.0.1
Flask-Login==0.6.2
""",
        'templates': {
            'base.html': """<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Учёт заявок{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
  {% block head %}{% endblock %}
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
    <div class="container">
      <a class="navbar-brand" href="{{ url_for('index') }}">Учёт заявок</a>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="nav-item"><a class="nav-link" href="{{ url_for('create_ticket') }}">Новая заявка</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('reset') }}">Обнулить данные</a></li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}">Выход</a></li>
        </ul>
      </div>
    </div>
  </nav>
  <div class="container">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script src="{{ url_for('static', filename='js/main.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
""",
            'index.html': """{% extends 'base.html' %}
{% block title %}Список заявок{% endblock %}
{% block content %}
<h2>Список заявок</h2>
<form method="get" class="row g-3 mb-4">
  <div class="col-md-2">
    <label for="date" class="form-label">Дата (ГГГГ-ММ-ДД)</label>
    <input type="text" name="date" id="date" class="form-control" placeholder="2025-01-31">
  </div>
  <div class="col-md-2">
    <label for="work" class="form-label">Тип работ</label>
    <select name="work" id="work" class="form-select">
      <option value="">Все</option>
      {% for work in work_types %}
        <option value="{{ work.id }}">{{ work.name }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-md-2">
    <label for="address" class="form-label">Адрес</label>
    <select name="address" id="address" class="form-select">
      <option value="">Все</option>
      {% for house in houses %}
        <option value="{{ house.id }}">{{ house.address }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-md-2">
    <label for="criticality" class="form-label">Критичность</label>
    <select name="criticality" id="criticality" class="form-select">
      <option value="">Все</option>
      <option value="Низкая">Низкая</option>
      <option value="Средняя">Средняя</option>
      <option value="Высокая">Высокая</option>
    </select>
  </div>
  <div class="col-md-2">
    <label for="status" class="form-label">Статус</label>
    <select name="status" id="status" class="form-select">
      <option value="">Все</option>
      <option value="Новая">Новая</option>
      <option value="В работе">В работе</option>
      <option value="Выполнена">Выполнена</option>
      <option value="Отменена">Отменена</option>
    </select>
  </div>
  <div class="col-md-2">
    <label for="employee" class="form-label">Исполнитель</label>
    <select name="employee" id="employee" class="form-select">
      <option value="">Все</option>
      {% for emp in employees %}
        <option value="{{ emp.id }}">{{ emp.name }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-md-2">
    <label for="responsible" class="form-label">Ответственный</label>
    <input type="text" name="responsible" id="responsible" class="form-control" placeholder="ФИО">
  </div>
  <div class="col-md-2 align-self-end">
    <button type="submit" class="btn btn-primary">Применить фильтры</button>
  </div>
</form>
<table class="table table-bordered">
  <thead>
    <tr>
      <th>Номер заявки</th>
      <th>Дата создания</th>
      <th>Описание</th>
      <th>Адрес</th>
      <th>Критичность</th>
      <th>Контакт</th>
      <th>Тип работ</th>
      <th>Статус</th>
      <th>Действия</th>
    </tr>
  </thead>
  <tbody>
    {% for ticket in tickets %}
    <tr>
      <td>{{ ticket.ticket_number }}</td>
      <td>{{ ticket.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
      <td>{{ ticket.description }}</td>
      <td>{{ ticket.address }}</td>
      <td>{{ ticket.criticality }}</td>
      <td>{{ ticket.contact_name }}<br>{{ ticket.contact_phone }}</td>
      <td>{{ ticket.work_type.name if ticket.work_type else '' }}</td>
      <td>{{ ticket.status }}</td>
      <td>
        <a href="{{ url_for('edit_ticket', ticket_id=ticket.id) }}" class="btn btn-sm btn-primary">Редактировать</a>
        <a href="{{ url_for('act', ticket_id=ticket.id) }}" class="btn btn-sm btn-secondary" target="_blank">Акт</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
""",
            'create_ticket.html': """{% extends 'base.html' %}
{% block title %}Новая заявка{% endblock %}
{% block content %}
<h2>Создание новой заявки</h2>
<form method="post">
  {{ form.hidden_tag() }}
  <div class="mb-3">
    {{ form.ticket_number.label(class="form-label") }}
    {{ form.ticket_number(class="form-control") }}
  </div>
  <div class="mb-3">
    {{ form.description.label(class="form-label") }}
    {{ form.description(class="form-control", rows=4) }}
  </div>
  <div class="mb-3">
    {{ form.address.label(class="form-label") }}
    {{ form.address(class="form-select") }}
  </div>
  <div class="mb-3">
    {{ form.criticality.label(class="form-label") }}
    {{ form.criticality(class="form-select") }}
  </div>
  <div class="mb-3">
    {{ form.contact_name.label(class="form-label") }}
    {{ form.contact_name(class="form-control") }}
  </div>
  <div class="mb-3">
    {{ form.contact_phone.label(class="form-label") }}
    {{ form.contact_phone(class="form-control") }}
  </div>
  <div class="mb-3">
    {{ form.work_type.label(class="form-label") }}
    {{ form.work_type(class="form-select") }}
  </div>
  <button type="submit" class="btn btn-success">{{ form.submit.label.text }}</button>
</form>
{% endblock %}
""",
            'edit_ticket.html': """{% extends 'base.html' %}
{% block title %}Редактировать заявку{% endblock %}
{% block content %}
<h2>Редактирование заявки № {{ ticket.ticket_number }}</h2>
<form method="post">
  {{ form.hidden_tag() }}
  <div class="mb-3">
    {{ form.status.label(class="form-label") }}
    {{ form.status(class="form-select") }}
  </div>
  <div class="mb-3">
    {{ form.start_time.label(class="form-label") }}
    {{ form.start_time(class="form-control", placeholder="2025-01-31 09:00") }}
  </div>
  <div class="mb-3">
    {{ form.end_time.label(class="form-label") }}
    {{ form.end_time(class="form-control", placeholder="2025-01-31 18:00") }}
  </div>
  <div class="mb-3">
    {{ form.assigned_employee.label(class="form-label") }}
    {{ form.assigned_employee(class="form-select") }}
  </div>
  <div class="mb-3">
    {{ form.responsible_person.label(class="form-label") }}
    {{ form.responsible_person(class="form-control") }}
  </div>
  <button type="submit" class="btn btn-primary">{{ form.submit.label.text }}</button>
</form>
{% endblock %}
""",
            'act.html': """<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Акт выполненных работ - Заявка {{ ticket.ticket_number }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    @media print { .no-print { display: none; } }
    .act-container { margin: 20px; }
  </style>
</head>
<body>
<div class="act-container">
  <h2 class="text-center">Акт выполненных работ</h2>
  <hr>
  <p><strong>Номер заявки:</strong> {{ ticket.ticket_number }}</p>
  <p><strong>Дата создания заявки:</strong> {{ ticket.created_at.strftime('%Y-%m-%d %H:%M') }}</p>
  <p><strong>Описание проблемы:</strong><br>{{ ticket.description }}</p>
  <p><strong>Адрес объекта:</strong> {{ ticket.address }}</p>
  <p><strong>Тип работ:</strong> {{ ticket.work_type.name if ticket.work_type else '' }}</p>
  <p><strong>Исполнитель:</strong> {{ ticket.assigned_employee.name if ticket.assigned_employee else '' }}</p>
  <p><strong>Время начала работы:</strong> {{ ticket.start_time.strftime('%Y-%m-%d %H:%M') if ticket.start_time else '' }}</p>
  <p><strong>Время окончания работы:</strong> {{ ticket.end_time.strftime('%Y-%m-%d %H:%M') if ticket.end_time else '' }}</p>
  <p><strong>Ответственный (мастер смены):</strong> {{ ticket.responsible_person }}</p>
  <hr>
  <p>Подписи сторон:</p>
  <p>Исполнитель: ______________________</p>
  <p>Заказчик: __________________________</p>
  <button class="btn btn-primary no-print" onclick="window.print()">Распечатать</button>
</div>
</body>
</html>
""",
            'reset.html': """{% extends 'base.html' %}
{% block title %}Обнуление данных{% endblock %}
{% block content %}
<h2>Обнуление данных</h2>
<p class="text-danger">ВНИМАНИЕ: Это действие удалит ВСЕ данные из базы (заявки, сотрудники, дома и типовые работы).</p>
<form method="post">
  <button type="submit" class="btn btn-danger">Подтвердить обнуление</button>
  <a href="{{ url_for('index') }}" class="btn btn-secondary">Отмена</a>
</form>
{% endblock %}
""",
            'login.html': """{% extends 'base.html' %}
{% block title %}Вход{% endblock %}
{% block content %}
<h2>Вход</h2>
<form method="post">
  {{ form.hidden_tag() }}
  <div class="mb-3">
    {{ form.username.label(class="form-label") }}
    {{ form.username(class="form-control") }}
  </div>
  <div class="mb-3">
    {{ form.password.label(class="form-label") }}
    {{ form.password(class="form-control") }}
  </div>
  <button type="submit" class="btn btn-primary">{{ form.submit.label.text }}</button>
</form>
{% endblock %}
"""
        },
        'static': {
            'css': {
                'custom.css': """body {
  padding-top: 20px;
}
"""
            },
            'js': {
                'main.js': """// пустой файл
"""
            }
        }
    }
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

if __name__ == '__main__':
    create_structure(os.getcwd(), project_structure)
    print("Структура проекта создана.")