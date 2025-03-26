from flask import Blueprint, render_template, redirect, jsonify
from datetime import datetime, timedelta
import json
from flask_login import login_required, current_user
from app.models import SensorReading
from sqlalchemy import func

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


@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

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
