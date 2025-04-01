from flask import Blueprint, render_template, redirect, jsonify, flash, request, url_for
from datetime import datetime, timedelta
import json
from flask_login import login_required, current_user
from app.models import SensorReading, SystemSetting
from sqlalchemy import func
from flask import Response
from app.camera import generate_frames
from app.forms import TemperatureSettingsForm
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


#@main.route('/video_feed')
#@login_required
#def video_feed():
#    """
#    Route that returns a Response streaming the video frames
#    Uses multipart/x-mixed-replace to continuously update the image
#    """
#    return Response(generate_frames(), 
#                    mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route('/video_feed')
@login_required
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# Commenting out the OG settings in case we have a problem.
#
#@main.route('/settings')
#@login_required
#def settings():
#    return render_template('settings.html')

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    temperature_form = TemperatureSettingsForm()

    if request.method == 'POST':
        setting_type = request.form.get('setting_type')
        
        if setting_type == 'temperature' and temperature_form.validate_on_submit():
            # Save temperature settings
            save_system_setting('temperature', 'min', temperature_form.temp_min.data)
            save_system_setting('temperature', 'max', temperature_form.temp_max.data)
            flash('Temperature settings updated successfully!', 'success')
            return redirect(url_for('main.settings'))
    
    # Load current settings
    temp_min = get_system_setting('temperature', 'min', default=60)
    temp_max = get_system_setting('temperature', 'max', default=80)
    temperature_form.temp_min.data = temp_min
    temperature_form.temp_max.data = temp_max
    
    return render_template('settings.html', 
                          temperature_form=temperature_form)

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
