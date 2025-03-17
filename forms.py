from flask_wtf import FlaskForm, RecaptchaField
from db import Users
import re
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    login = StringField("Имя: ", validators=[DataRequired(),Length(min=4, max=20, message="Имя должно быть от 4 до 100 символов")])
    psw = PasswordField("Пароль: ", validators=[DataRequired(),
                                                Length(min=4, max=100, message="Пароль должен быть от 4 до 100 символов")])
    remember = BooleanField("Запомнить", default = False)
    submit = SubmitField("Войти", render_kw={'class': 'login_button'})

class RegisterForm(FlaskForm):
    login = StringField("Имя: ", validators=[Length(min=4, max=20, message="Имя должно быть от 4 до 100 символов")])
    name = StringField("Имя: ", validators=[Length(min=4, max=100, message="Имя должно быть от 4 до 100 символов")])
    email = StringField("Email: ", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль: ", validators=[DataRequired(),
                                                Length(min=4, max=100, message="Пароль должен быть от 4 до 100 символов")])
    recaptcha  = RecaptchaField()
    psw2 = PasswordField("Повтор пароля: ", validators=[DataRequired(), EqualTo('psw', message="Пароли не совпадают")])
    submit = SubmitField("Регистрация", render_kw={'class': 'login_button'})

    def validate_login(self, field):
        if Users.query.filter_by(login=field.data).first():
            raise ValueError("1")

        if not re.match(r"^[a-zA-Z0-9_]+$", field.data):
            raise ValueError("2")

    def validate_email(self, field):
        if Users.query.filter_by(email=field.data).first():
            raise ValueError("3")