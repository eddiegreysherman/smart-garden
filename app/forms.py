from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TimeField, SelectField, BooleanField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional
from app.models import User
from flask_login import current_user

class RegistrationForm(FlaskForm):
    """
    Form for new user registration.
    Collects username, email, and password with confirmation.
    Includes validation for username uniqueness and password strength.
    """
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
        """
        Custom validator to ensure username uniqueness.
        Checks if the username already exists in the database.
        
        Args:
            username: The username field to validate
            
        Raises:
            ValidationError: If username is already taken
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        """
        Custom validator to ensure email uniqueness.
        Checks if the email is already registered in the database.
        
        Args:
            email: The email field to validate
            
        Raises:
            ValidationError: If email is already registered
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    """
    Form for user login.
    Collects email and password for authentication.
    """
    email = StringField('Email',
        validators=[
            DataRequired(),
            Email(message="Invalid email address")
        ])
    password = PasswordField('Password',
        validators=[DataRequired()])
    submit = SubmitField('Login')

class TemperatureSettingsForm(FlaskForm):
    """
    Form for configuring temperature thresholds.
    Sets minimum and maximum acceptable temperature values for the garden environment.
    Range constrained to prevent extreme values.
    """
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
    """
    Form for configuring humidity thresholds.
    Sets minimum and maximum acceptable humidity levels for the garden environment.
    Range constrained between 0-100%.
    """
    humidity_min = FloatField('Minimum Humidity (%)', 
        validators=[
            DataRequired(),
            NumberRange(min=0, max=100)
        ])
    humidity_max = FloatField('Maximum Humidity (%)', 
        validators=[
            DataRequired(),
            NumberRange(min=0, max=100)
        ])
    submit = SubmitField('Save Settings')

class CO2SettingsForm(FlaskForm):
    """
    Form for configuring CO2 level thresholds.
    Sets minimum and maximum acceptable CO2 concentration in parts per million.
    Range constrained to prevent unhealthy or unrealistic values.
    """
    co2_min = FloatField('Minimum CO2 (PPM)', 
        validators=[
            DataRequired(),
            NumberRange(min=0, max=500)
        ])
    co2_max = FloatField('Maximum CO2 (PPM)', 
        validators=[
            DataRequired(),
            NumberRange(min=500, max=4000)
        ])
    submit = SubmitField('Save Settings')

class LightSettingsForm(FlaskForm):
    """
    Form for configuring light schedule.
    Sets daily on and off times for grow lights.
    Includes validation to prevent identical on/off times.
    """
    light_on_time = TimeField('Lights On Time',
        validators=[DataRequired()])
    light_off_time = TimeField('Lights Off Time',
        validators=[DataRequired()])
    submit = SubmitField('Save Settings')

    def validate_light_off_time(self, field):
        """
        Custom validator to ensure on and off times are not identical.
        Converts times to minutes since midnight for comparison.
        
        Args:
            field: The light_off_time field to validate
            
        Raises:
            ValidationError: If on and off times are the same
        """
        if self.light_on_time.data and field.data:
            # Convert both times to minutes since midnight for comparison
            on_minutes = self.light_on_time.data.hour * 60 + self.light_on_time.data.minute
            off_minutes = field.data.hour * 60 + field.data.minute
            if on_minutes == off_minutes:
                raise ValidationError('On and Off times cannot be the same')

class MoistureSettingsForm(FlaskForm):
    """
    Form for configuring soil moisture thresholds and watering parameters.
    Sets minimum acceptable moisture level and how long to run the water pump.
    Range constraints prevent overwatering or system damage.
    """
    moisture_min = FloatField('Minimum Moisture Level (%)', 
        validators=[DataRequired(), NumberRange(min=0, max=100)])
    pump_duration = IntegerField('Pump Duration (seconds)', 
        validators=[DataRequired(), NumberRange(min=1, max=300)])  # Example max of 5 minutes
    submit = SubmitField('Save Settings')

class UserSettingsForm(FlaskForm):
    """
    Form for updating user account settings.
    Allows changing email address, password, and notification preferences.
    Password change is optional - fields can be left blank to keep current password.
    """
    email = StringField('Email Address', 
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address")
        ])
    new_password = PasswordField('New Password',
        validators=[
            Optional(),  # Password is optional
            Length(min=8, message="Password must be at least 8 characters")
        ])
    confirm_password = PasswordField('Confirm New Password',
        validators=[
            EqualTo('new_password', message='Passwords must match')
        ])
    enable_alerts = BooleanField('Enable Email Alerts')
    submit = SubmitField('Save Settings')

    def validate_email(self, email):
        """
        Custom validator to ensure email uniqueness when changing email address.
        Only checks database if the email differs from the user's current email.
        
        Args:
            email: The email field to validate
            
        Raises:
            ValidationError: If new email is already registered to another user
        """
        if email.data != current_user.email:  # Only check if email is being changed
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered.')
