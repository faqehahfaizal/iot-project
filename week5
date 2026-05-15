import os
import time
import logging
import sqlite3
from datetime import datetime
import board
import adafruit_dht

# 1. Configuration
# On Pi 5, we use 'board' to define pins (e.g., board.D4 for GPIO 4)
PIN = board.D4 
DB_FILE = "sensor_data.db"
LOG_INTERVAL = 10  

# Initialize the DHT11 device
dhtDevice = adafruit_dht.DHT11(PIN)

def init_database():
    # Change this line in your functions:
    conn = sqlite3.connect(DB_FILE, timeout=0)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def read_dht11():
    """Read data using the CircuitPython library logic"""
    try:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        if temperature is not None and humidity is not None:
            return round(temperature, 1), round(humidity, 1)
    except RuntimeError as error:
        # Errors are common with DHT sensors; just log and continue
        logging.warning(f"Sensor reading error: {error.args[0]}")
    except Exception as error:
        dhtDevice.exit()
        raise error
    return None, None

def save_reading(temperature, humidity):
    # Change this line in your functions:
    conn = sqlite3.connect(DB_FILE, timeout=0)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
        (timestamp, temperature, humidity)
    )
    conn.commit()
    conn.close()
    logging.info(f"Saved: {temperature}C, {humidity}%")

# 2. Main Execution Loop
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
    
    print("Starting DHT11 Logger on Raspberry Pi 5...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            temp, hum = read_dht11()
            
            if temp is not None and hum is not None:
                save_reading(temp, hum)
                print(f"Success - Temp: {temp}C, Hum: {hum}%")
            
            # DHT11 sensors need a decent gap between readings to stay stable
            time.sleep(LOG_INTERVAL)
            
    except KeyboardInterrupt:
        dhtDevice.exit()
        print("\nLogging stopped.")
