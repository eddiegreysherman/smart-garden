from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TimeField, SelectField, BooleanField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username',
        validators=[
            DataRequired(),
            Length(min=3, max=50,
            message="Username must be between 3 and 50 characters")
        ])
    email = StringField('Email',
        validators=[
            DataRequired(),
            Email(message="Invalid email address")
        ])
    password = PasswordField('Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters")
        ])
    confirm_password = PasswordField('Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message="Passwords must match")
        ])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email',
        validators=[
            DataRequired(),
            Email(message="Invalid email address")
        ])
    password = PasswordField('Password',
        validators=[DataRequired()])
    submit = SubmitField('Login')

class TemperatureSettingsForm(FlaskForm):
    temp_min = FloatField('Minimum Temperature (°F)', 
        validators=[
            DataRequired(),
            NumberRange(min=50, max=65)
        ])
    temp_max = FloatField('Maximum Temperature (°F)', 
        validators=[
            DataRequired(),
            NumberRange(min=66, max=99)
        ])
    submit = SubmitField('Save Settings')

class HumiditySettingsForm(FlaskForm):
    humidity_min = IntegerField('Minimum Humidity (%)', 
        validators=[
            DataRequired(),
            NumberRange(min=0, max=100)
        ])
    humidity_max = IntegerField('Maximum Humidity (%)', 
        validators=[
            DataRequired(),
            NumberRange(min=0, max=100)
        ])
    submit = SubmitField('Save Settings')

class CO2SettingsForm(FlaskForm):
    co2_min = IntegerField('Minimum CO2 (PPM)', 
        validators=[
            DataRequired(),
            NumberRange(min=0, max=500)
        ])
    co2_max = IntegerField('Maximum CO2 (PPM)', 
        validators=[
            DataRequired(),
            NumberRange(min=500, max=4000)
        ])
    submit = SubmitField('Save Settings')
