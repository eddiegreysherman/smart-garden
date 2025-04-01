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

# Form for temp settings and validation
class TemperatureSettingsForm(FlaskForm):
    setting_type = HiddenField('Setting Type', default='temperature')
    temp_min = FloatField('Minimum Temperature (°F)', 
        validators=[
            DataRequired(),
            NumberRange(min=50, max=65, message="Temperature must be between 50°F and 65°F")
        ])
    temp_max = FloatField('Maximum Temperature (°F)', 
        validators=[
            DataRequired(),
            NumberRange(min=66, max=99, message="Temperature must be between 66°F and 99°F")
        ])
    submit = SubmitField('Save Temperature Settings')

    def validate_temp_max(self, temp_max):
        if temp_max.data <= self.temp_min.data:
            raise ValidationError('Maximum temperature must be greater than minimum temperature')
