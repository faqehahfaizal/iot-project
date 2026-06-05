import board
import adafruit_dht
import sqlite3
from datetime import datetime
import time
import socket
import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Configuration
DB_FILE = "sensor_data.db"
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN")
BLYNK_BASE = "https://blynk.cloud/external/api"

READ_INTERVAL = 5.0


def init_database():
    """Initialize database schema to store sensor readings."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_reading(temperature, humidity):
    """Save sensor reading to local SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
        (timestamp, temperature, humidity)
    )

    conn.commit()
    conn.close()


def is_wifi_connected():
    """Check if Raspberry Pi has internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False


def send_to_blynk(temp, humidity):
    """Send temperature and humidity to Blynk Cloud using HTTP API."""
    if not BLYNK_AUTH:
        raise RuntimeError("BLYNK_AUTH_TOKEN not found in .env file")

    # Send temperature to V0
    r1 = requests.get(
        f"{BLYNK_BASE}/update",
        params={
            "token": BLYNK_AUTH,
            "V0": temp
        },
        timeout=5
    )
    r1.raise_for_status()

    # Send humidity to V1
    r2 = requests.get(
        f"{BLYNK_BASE}/update",
        params={
            "token": BLYNK_AUTH,
            "V1": humidity
        },
        timeout=5
    )
    r2.raise_for_status()


if __name__ == "__main__":
    init_database()

    # DHT11 data pin connected to GPIO 4, physical pin 7
    dhtDevice = adafruit_dht.DHT11(board.D4)

    print("Week 7 DHT11 + SQLite + Blynk Cloud started.")
    print("Press Ctrl+C to stop.")

    last_read_time = 0

    try:
        while True:
            current_time = time.time()

            if current_time - last_read_time >= READ_INTERVAL:
                last_read_time = current_time

                try:
                    temp = dhtDevice.temperature
                    hum = dhtDevice.humidity

                    if temp is not None and hum is not None:
                        temp = float(temp)
                        hum = float(hum)

                        print(f"Temperature: {temp:.1f}C, Humidity: {hum:.1f}%")

                        # Always save locally first
                        save_reading(temp, hum)
                        print("Data saved to local database.")

                        # Try sending to Blynk
                        if is_wifi_connected():
                            try:
                                send_to_blynk(temp, hum)
                                print("Data sent to Blynk!")
                            except requests.exceptions.Timeout:
                                print("Blynk timeout. Data saved locally only.")
                            except requests.exceptions.ConnectionError:
                                print("Network/Blynk connection error. Data saved locally only.")
                            except Exception as e:
                                print(f"Blynk error: {e}. Data saved locally only.")
                        else:
                            print("Wi-Fi offline. Data saved locally only.")

                    else:
                        print("Failed to read sensor: value is None")

                except RuntimeError:
                    # DHT11 sometimes fails temporarily; ignore and retry
                    pass
                except Exception as e:
                    print(f"Sensor error: {e}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")

    finally:
        dhtDevice.exit()