from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, TextField, PasswordField, BooleanField
from wtforms.validators import Required, EqualTo, Email

from app.users.models import User


class LoginForm(Form):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(Form):
    name = TextField('NickName', [Required()])
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Repeat Password', [
        Required(),
        EqualTo('password', message='Passwords must match')
    ])
    accept_tos = BooleanField('I accept the TOS', [Required()])
    recaptcha = RecaptchaField()


class EditForm(Form):
    name = StringField('Name', [Required()])
    about_me = TextField('About me', [Required()])

    def __init__(self, original_name, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_name = original_name

    def validate(self):
        if not Form.validate(self):
            return False
        if self.name.data == self.original_name:
            return True
        user = User.query.filter_by(name=self.name.data).first()
        if user != None:
            self.name.errors.append('This name is already in use. Please choose another one.')
            return False
        return True


class PostForm(Form):
    post = StringField('post', validators=[Required()])


class SearchForm(Form):
    search = StringField('search', validators=[Required()])
