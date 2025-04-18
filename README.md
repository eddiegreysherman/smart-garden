# 🍅 Smart Garden

A Flask-based monitoring and automation system for indoor grow environments using a Raspberry Pi.

## 🔧 Key Components

- Web Interface (Flask + HTMX)
- SCD41 Environmental Sensor (CO₂, Temp, Humidity)
- Soil Moisture Sensor Probe
- Relay-controlled:
  - Water Pump
  - LED Grow Light
  - Duct Fan(s)
- SQLite Database
- USB Camera Feed (Live MJPEG stream)

---

## 🚀 Installation Guide

### 🖥 System Requirements

- Raspberry Pi OS / Debian-based Linux
- Python 3.8+
- SSH enabled
- I2C enabled (via `raspi-config`)
- USB Camera
- (Optional) Reverse proxy server with Nginx and Cloudflare Tunnel for external access

---

### ⚙️ Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/eddiegreysherman/smart-garden.git
   cd smart-garden
   ```

2. **Set Up Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Initialize the Database**

   The database will automatically be created on first launch. It includes tables for:
   - Users
   - Sensor readings
   - System settings

---
## 🔌 Systemd Services

Two systemd services manage background tasks:

---

### 1. `scd41-sensor.service` (for continuous sensor readings)

This service reads CO₂, temperature, and humidity data from the SCD41 sensor and writes it to the SQLite database.

#### Create systemd service:
```bash
sudo cp systemd/scd41.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scd41.service
sudo systemctl start scd41.service
```

#### Contents of `systemd/scd41.service`:
```ini
[Unit]
Description=SCD41 CO2 Sensor Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/smart-garden
ExecStart=/home/YOUR_USERNAME/smart-garden/venv/bin/python -m app.utils.scd41
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=scd41-sensor

[Install]
WantedBy=multi-user.target
```

---

### 2. `smart-garden.service` (for control logic execution)

This service controls the relays for fan, light, and pump based on sensor data and threshold settings.

#### Before enabling, ensure `/var/log/smart-garden/` exists and is writable:

```bash
sudo mkdir -p /var/log/smart-garden
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/log/smart-garden
```

#### Create systemd service:
```bash
sudo cp systemd/smart-garden.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smart-garden.service
sudo systemctl start smart-garden.service
```

#### Contents of `systemd/smart-garden.service`:
```ini
[Unit]
Description=Smart Garden Control System
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/smart-garden
Environment="PYTHONPATH=/home/YOUR_USERNAME/smart-garden"
Environment="PATH=/home/YOUR_USERNAME/smart-garden/venv/bin"
ExecStart=/home/YOUR_USERNAME/smart-garden/venv/bin/python /home/YOUR_USERNAME/smart-garden/app/control.py
Restart=always

[Install]
WantedBy=multi-user.target
```

> Replace `YOUR_USERNAME` with the Linux user that owns and runs the project directory.

---

## 🌐 Running the Web Server

```bash
source venv/bin/activate
flask run -h 0.0.0.0
```

Then visit: [http://your_pi_ip:5000](http://your_pi_ip:5000)

---

## 🧭 App Structure

### 1. Dashboard
- Real-time:
  - Temperature (°F)
  - Humidity (%)
  - CO₂ levels (ppm)
  - Moisture status
- Device Status:
  - Light / Fan / Pump (On/Off)
- Charts:
  - 48-hour Temp + Humidity (Chart.js)
- Camera Feed (MJPEG)

### 2. Settings Page
- Thresholds:
  - Temperature, Humidity, CO₂
- Light Schedule:
  - Set ON / OFF times
- User Settings:
  - Change password
  - Set alerts
- Admin Features:
  - Add/Remove users

---

## 📊 Architecture Overview

### 🔄 Data Flow

| Source                | Frequency   | Function                          |
|-----------------------|-------------|-----------------------------------|
| `/app/utils/scd41.py` (systemd)      | Every 30s   | Sensor read → DB insert           |
| `/app/control.py` (systemd)| Every 1 min| Threshold check (10 min avg) → Relay control   |
| Web UI                | On demand   | User settings & camera stream     |

### 💡 Technology Stack

| Component      | Tech                         |
|----------------|------------------------------|
| Web Framework  | Flask                        |
| Frontend       | Bootstrap, HTMX, Chart.js    |
| Sensor Comm    | `python-scd4x` (I2C)          |
| GPIO Control   | RPi.GPIO                     |
| Database       | SQLite                       |
| Background     | systemd services             |

---

## 🧪 Daily Operations

- Monitor readings via Dashboard
- Adjust environmental thresholds via Settings
- Set automated light cycles
- Add or manage users as admin

---

## 🛠 Maintenance & Backups

- **Sensor Logs:**  
  ```bash
  journalctl -u scd41.service -n 50 --no-pager
  ```

- **Database Backup:**  
  ```bash
  sqlite3 instance/smartgarden.db .dump > backup.sql
  ```

- Regular checks:
  - Sensor accuracy (monthly)
  - Password updates (quarterly)

---

## 🧯 Troubleshooting

| Issue                        | Solution                                             |
|------------------------------|------------------------------------------------------|
| Sensor not updating          | Check `scd41.service` status, verify wiring          |
| Relays not triggering        | Check GPIO pins and control thresholds              |
| Light schedule ignored       | Ensure correct timezone, browser cache cleared       |
| Permission denied writing logs | Ensure `/var/log/smart-garden` is writable         |

---

## 📸 Screenshots

> Coming soon – the project is under active development!

---

## 📢 Notes

- Some features like light intensity control are placeholders for future enhancements.
- Application is in active development – contributions & feedback welcome!
