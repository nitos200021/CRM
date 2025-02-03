from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class HouseForm(FlaskForm):
    address = StringField('Адрес дома', validators=[DataRequired()])
    floors = StringField('Количество этажей')
    submit = SubmitField('Добавить адрес')

class WorkTypeForm(FlaskForm):
    name = StringField('Название типа работы', validators=[DataRequired()])
    description = TextAreaField('Описание')
    submit = SubmitField('Добавить тип работы')
    
class EmployeeForm(FlaskForm):
    name = StringField('Имя исполнителя', validators=[DataRequired()])
    position = StringField('Должность', validators=[DataRequired()])
    submit = SubmitField('Добавить исполнителя')