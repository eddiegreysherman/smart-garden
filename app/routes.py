from flask import Blueprint, render_template, redirect, jsonify, flash, request, url_for
from datetime import datetime, timedelta
import json
from flask_login import login_required, current_user
from app.models import SensorReading, SystemSetting
from sqlalchemy import func
from flask import Response
from app.camera import generate_frames
from app.forms import TemperatureSettingsForm, HumiditySettingsForm, CO2SettingsForm, LightSettingsForm, UserSettingsForm, MoistureSettingsForm
from app import db

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return redirect('/dashboard')

@main.route('/dashboard')
@login_required
def dashboard():
    # Get the latest sensor reading
    reading = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()

    # Get statuses for indicators fan, lights, and pump
    light_on_time = get_system_setting('light', 'on_time', default='06:00')
    light_off_time = get_system_setting('light', 'off_time', default='20:00')
    fan_on_temp = get_system_setting('temperature', 'max', default=75)  # Turn on when above this
    fan_on_humidity = get_system_setting('humidity', 'max', default=70) 
    pump_on_moisture = get_system_setting('moisture', 'min', default=30)  # Turn on when below this

    # Convert current time and settings to comparable format
    current_time = datetime.now().strftime('%H:%M')
    
    fan_on = False
    pump_on = False
    if reading:
        fan_on = (reading.temperature > fan_on_temp) or (reading.humidity > fan_on_humidity)
        pump_on = reading.moisture < pump_on_moisture

    # Check if lights should be on
    if light_on_time <= light_off_time:
        # Simple case: on_time is before off_time in the same day
        lights_on = light_on_time <= current_time <= light_off_time
    else:
        # Complex case: on_time is after off_time (spans midnight)
        lights_on = current_time >= light_on_time or current_time <= light_off_time

    return render_template('dashboard.html',
                        current_user=current_user,
                        reading=reading,
                        lights_on=lights_on,
                        fan_on=fan_on,
                        pump_on=pump_on,
                        chart_title="Last 48 Hours")


@main.route('/video_feed')
@login_required
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@main.route('/settings')
@login_required
def settings():
    current_settings = {
        'temperature': {
            'min': get_system_setting('temperature', 'min', default=65),
            'max': get_system_setting('temperature', 'max', default=75)
        },
        'humidity': {
            'min': get_system_setting('humidity', 'min', default=40),
            'max': get_system_setting('humidity', 'max', default=80)
        },
        'co2': {
            'min': get_system_setting('co2', 'min', default=400),
            'max': get_system_setting('co2', 'max', default=1500)
        },
        'light': {
            'on_time': get_system_setting('light', 'on_time', default='06:00'),
            'off_time': get_system_setting('light', 'off_time', default='20:00')
        },
        'user': {
            'email': current_user.email,
            'alerts_enabled': get_system_setting('user', 'alerts_enabled', default='true')
        },
        'moisture': {
            'min': get_system_setting('moisture', 'min', default='30'),
            'max': get_system_setting('moisture', 'max', default='80')
        }
    }

    return render_template('settings/index.html', 
                         current_settings=current_settings)

@main.route('/settings/temperature', methods=['GET', 'POST'])
@login_required
def temperature_settings():
    form = TemperatureSettingsForm()
    
    if form.validate_on_submit():
        save_system_setting('temperature', 'min', form.temp_min.data)
        save_system_setting('temperature', 'max', form.temp_max.data)
        flash('Temperature settings updated successfully!', 'success')
        return redirect(url_for('main.temperature_settings'))

    # Load current settings
    form.temp_min.data = get_system_setting('temperature', 'min', default=65)
    form.temp_max.data = get_system_setting('temperature', 'max', default=75)
    
    return render_template('settings/temperature.html', form=form)

@main.route('/settings/humidity', methods=['GET', 'POST'])
@login_required
def humidity_settings():
    form = HumiditySettingsForm()
    
    if form.validate_on_submit():
        save_system_setting('humidity', 'min', form.humidity_min.data)
        save_system_setting('humidity', 'max', form.humidity_max.data)
        flash('Humidity settings updated successfully!', 'success')
        return redirect(url_for('main.humidity_settings'))

    # Load current settings
    form.humidity_min.data = get_system_setting('humidity', 'min', default=40)
    form.humidity_max.data = get_system_setting('humidity', 'max', default=80)
    
    return render_template('settings/humidity.html', form=form)

@main.route('/settings/co2', methods=['GET', 'POST'])
@login_required
def co2_settings():
    form = CO2SettingsForm()
    
    if form.validate_on_submit():
        save_system_setting('co2', 'min', form.co2_min.data)
        save_system_setting('co2', 'max', form.co2_max.data)
        flash('CO2 settings updated successfully!', 'success')
        return redirect(url_for('main.co2_settings'))

    # Load current settings
    form.co2_min.data = get_system_setting('co2', 'min', default=400)
    form.co2_max.data = get_system_setting('co2', 'max', default=1800)
    
    return render_template('settings/co2.html', form=form)

@main.route('/settings/light', methods=['GET', 'POST'])
@login_required
def light_settings():
    form = LightSettingsForm()
    
    if form.validate_on_submit():
        # Convert time objects to string for storage (HH:MM format)
        on_time = form.light_on_time.data.strftime('%H:%M')
        off_time = form.light_off_time.data.strftime('%H:%M')
        
        save_system_setting('light', 'on_time', on_time)
        save_system_setting('light', 'off_time', off_time)
        flash('Light schedule updated successfully!', 'success')
        return redirect(url_for('main.light_settings'))

    # Load current settings
    on_time_str = get_system_setting('light', 'on_time', default='06:00')
    off_time_str = get_system_setting('light', 'off_time', default='20:00')
    
    # Convert string times to time objects for the form
    from datetime import datetime
    form.light_on_time.data = datetime.strptime(on_time_str, '%H:%M').time()
    form.light_off_time.data = datetime.strptime(off_time_str, '%H:%M').time()

    return render_template('settings/light.html', form=form)


@main.route('/settings/moisture', methods=['GET', 'POST'])
@login_required
def moisture_settings():
    form = MoistureSettingsForm()
    
    if form.validate_on_submit():
        save_system_setting('moisture', 'min', form.moisture_min.data)
        save_system_setting('moisture', 'max', form.moisture_max.data)
        flash('Moisture settings updated successfully!', 'success')
        return redirect(url_for('main.moisture_settings'))

    # Load current settings
    form.moisture_min.data = get_system_setting('moisture', 'min', default=30)
    form.moisture_max.data = get_system_setting('moisture', 'max', default=80)
    
    return render_template('settings/moisture.html', form=form)

@main.route('/settings/user', methods=['GET', 'POST'])
@login_required
def user_settings():
    form = UserSettingsForm()

    if form.validate_on_submit():
        # Handle email change
        if form.email.data != current_user.email:
            current_user.email = form.email.data
            flash('Email updated successfully!', 'success')

        # Handle password change
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            flash('Password updated successfully!', 'success')

        # Handle alert settings
        save_system_setting('user', 'alerts_enabled', 
                          'true' if form.enable_alerts.data else 'false')

        db.session.commit()
        return redirect(url_for('main.user_settings'))

    # Load current settings
    form.email.data = current_user.email
    form.enable_alerts.data = get_system_setting('user', 'alerts_enabled', default='true')
    return render_template('settings/user.html', form=form)

def save_system_setting(setting_type, key, value):
    """Save a system-wide setting to the database"""
    # Check if setting exists
    setting = SystemSetting.query.filter_by(
        setting_type=setting_type,
        key=key
    ).first()

    if setting:
        # Update existing setting
        setting.value = str(value)
    else:
        # Create new setting
        setting = SystemSetting(
            setting_type=setting_type,
            key=key,
            value=str(value)
        )
        db.session.add(setting)

    db.session.commit()

def get_system_setting(setting_type, key, default=None):
    """Get a system-wide setting from the database"""
    setting = SystemSetting.query.filter_by(
        setting_type=setting_type,
        key=key
    ).first()

    if setting:
        # Try to convert to the appropriate type
        try:
            # First try to convert to float
            return float(setting.value)
        except ValueError:
            # If that fails, check if it's a boolean
            if setting.value.lower() in ('true', 'false'):
                return setting.value.lower() == 'true'
            # Otherwise return as string
            return setting.value
    return default

@main.route('/current-readings')
@login_required
def current_readings():
    # Get the latest sensor reading
    reading = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()

    # Get light schedule from settings
    light_on_time = get_system_setting('light', 'on_time', default='06:00')
    light_off_time = get_system_setting('light', 'off_time', default='20:00')
    fan_on_temp = get_system_setting('temperature', 'max', default=75)  # Turn on when above this
    fan_on_humidity = get_system_setting('humidity', 'max', default=70)
    pump_on_moisture = get_system_setting('moisture', 'min', default=30)  # Turn on when below this

    # Convert current time and settings to comparable format
    current_time = datetime.now().strftime('%H:%M')

    fan_on = False
    pump_on = False
    if reading:
        fan_on = (reading.temperature > fan_on_temp) or (reading.humidity > fan_on_humidity)
        pump_on = reading.moisture < pump_on_moisture
    
    # Check if lights should be on
    if light_on_time <= light_off_time:
        lights_on = light_on_time <= current_time <= light_off_time
    else:
        lights_on = current_time >= light_on_time or current_time <= light_off_time

    return render_template('partials/current_readings.html',
                        reading=reading,
                        lights_on=lights_on,
                        fan_on=fan_on,
                        pump_on=pump_on)

@main.route('/api/chart-data')
@login_required
def chart_data():
    # Get readings from the last 48 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=48)

    # Get a list of all readings in the time period
    all_readings = SensorReading.query.filter(
        SensorReading.timestamp.between(start_time, end_time)
    ).order_by(SensorReading.timestamp.asc()).all()

    # Group readings by hour and select one reading per hour
    hourly_readings = {}
    for reading in all_readings:
        # Create a key for each hour
        hour_key = reading.timestamp.strftime('%Y-%m-%d %H')

        # Store only the first reading for each hour
        if hour_key not in hourly_readings:
            hourly_readings[hour_key] = reading

    # Convert to a sorted list
    readings = [hourly_readings[key] for key in sorted(hourly_readings.keys())]

    # Prepare data for the chart
    timestamps = [reading.timestamp.strftime('%Y-%m-%d %H:%M') for reading in readings]
    temperature_data = [reading.temperature for reading in readings]
    humidity_data = [reading.humidity for reading in readings]

    return jsonify({
        'timestamps': timestamps,
        'temperature': temperature_data,
        'humidity': humidity_data
    })
