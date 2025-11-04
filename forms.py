from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, PasswordField, DateField, SelectField
from wtforms.validators import InputRequired, NumberRange, Length, EqualTo

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=0, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8,max=50)])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Play')