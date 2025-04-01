from flask import Blueprint, render_template, redirect, jsonify, flash, request, url_for
from datetime import datetime, timedelta
import json
from flask_login import login_required, current_user
from app.models import SensorReading, SystemSetting
from sqlalchemy import func
from flask import Response
from app.camera import generate_frames
from app.forms import TemperatureSettingsForm, HumiditySettingsForm, CO2SettingsForm
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

    # Check if lights are on (you may need to adjust this logic based on your app)
    current_hour = datetime.now().hour
    lights_on = 6 <= current_hour <= 20

    return render_template('dashboard.html',
                          current_user=current_user,
                          reading=reading,
                          lights_on=lights_on,
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

    # Check if lights are on (you may need to adjust this logic based on your app)
    # For now, we'll assume lights are on during the day
    import datetime
    current_hour = datetime.datetime.now().hour
    lights_on = 6 <= current_hour <= 20

    return render_template('partials/current_readings.html',
                          reading=reading,
                          lights_on=lights_on)


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
