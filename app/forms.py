from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional
from app.models import User

from config import ALLOWED_EXTENSIONS



class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято.')



class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Войти')

class EditProfileForm(FlaskForm):
    avatar = FileField(f"Выберете аватарку ({ALLOWED_EXTENSIONS})", validators=[Optional()])
    submit = SubmitField('Сохранить изменения')

class CreatePostForm(FlaskForm):
    content = TextAreaField("text", validators=[DataRequired(), Length(min=1, max=500)])
    image = FileField(f"Выберете картинку ({ALLOWED_EXTENSIONS})", validators=[Optional()])
    submit = SubmitField('Опубликовать')


class AddCommentForm(FlaskForm):
    content = TextAreaField("text", validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Опубликовать')


class SendMessageForm(FlaskForm):
    content = TextAreaField("text", validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('→')


class SearchForm(FlaskForm):
    query = StringField("text", validators=[Optional(), Length(max=64)])
    submit = SubmitField('Найти')