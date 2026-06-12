import board
import adafruit_dht
import sqlite3
from datetime import datetime
import time
import socket
import os
import requests
from dotenv import load_dotenv

# Load .env file for security credentials
load_dotenv()

# Configuration
DB_FILE = "sensor_data.db"
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN")
BLYNK_BASE = "https://blynk.cloud/external/api"

# Interval settings as specified in Lab Guidelines
READ_INTERVAL = 5.0

def init_database():
    """Initialize database schema to store sensor readings with Week 9 sync status tracking."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Creates core schema layout with fallback tracking column structure built-in
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            synced INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_reading(temperature, humidity):
    """Save sensor reading to local SQLite database with synced status defaulted to 0 (unsent)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Inserts telemetry values with an explicit '0' flag indicating a dirty/unsynced cache block
    cursor.execute(
        "INSERT INTO readings (timestamp, temperature, humidity, synced) VALUES (?, ?, ?, 0)",
        (timestamp, temperature, humidity)
    )

    conn.commit()
    last_id = cursor.lastrowid  # Returns the exact primary key identifier for tracking tracking
    conn.close()
    return last_id


def mark_as_synced(reading_id):
    """Flip the tracking state of an edge-buffered record to 1 (successfully pushed)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE readings SET synced = 1 WHERE id = ?", (reading_id,))
    conn.commit()
    conn.close()


def is_wifi_connected():
    """Check if Raspberry Pi has internet connection via low-overhead DNS handshake."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False


def send_to_blynk(temp, humidity):
    """Send temperature and humidity to Blynk Cloud using HTTP API endpoints."""
    if not BLYNK_AUTH:
        raise RuntimeError("BLYNK_AUTH_TOKEN not found in your .env file!")

    # Synchronize Temperature parameter to Virtual Pin V0
    r1 = requests.get(
        f"{BLYNK_BASE}/update",
        params={
            "token": BLYNK_AUTH,
            "V0": temp
        },
        timeout=5
    )
    r1.raise_for_status()

    # Synchronize Humidity parameter to Virtual Pin V1
    r2 = requests.get(
        f"{BLYNK_BASE}/update",
        params={
            "token": BLYNK_AUTH,
            "V1": humidity
        },
        timeout=5
    )
    r2.raise_for_status()


def resend_unsynced():
    """Locate historical backlog gaps in the SQLite engine and dump them down the cloud pipeline."""
    if not is_wifi_connected():
        return  # Fast-exit safely if layer 3 transport interface handles are dead

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Target only older entries that have a dirty state flag equal to zero
    cursor.execute("SELECT id, temperature, humidity FROM readings WHERE synced = 0")
    rows = cursor.fetchall()

    if rows:
        print(f"\n[Backlog Manager] Found {len(rows)} unsynced entries in the buffer queue. Attempting recovery...")
        for row in rows:
            reading_id, temp, hum = row
            try:
                send_to_blynk(temp, hum)
                mark_as_synced(reading_id)
                print(f" -> Successfully flushed backlog record Reference ID: {reading_id}")
                time.sleep(0.5)  # Rate-limiting cushion to protect downstream Blynk ingress pipes
            except Exception as e:
                print(f" -> Backlog sync paused. Network environment remains unstable: {e}")
                break  # Break transaction processing early if pipe failures occur mid-run
    conn.close()


if __name__ == "__main__":
    init_database()

    # DHT11 data pin connected to GPIO 4, physical pin 7
    dhtDevice = adafruit_dht.DHT11(board.D4)

    print("=====================================================")
    print(" Week 9 Production-Ready Resilient IoT Monitor Active ")
    print("=====================================================")
    print("Press Ctrl+C to safely stop application loops.\n")

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

                        print(f"\n[Sensor Read] Telemetry Sampled: Temp={temp:.1f}C | Hum={hum:.1f}%")

                        # STEP 1: Always cache payload metrics locally first (Sets synced = 0)
                        reading_id = save_reading(temp, hum)
                        print(f" -> Local Storage Commit Success (Row ID: {reading_id})")

                        # STEP 2: Try real-time foreground ingestion
                        if is_wifi_connected():
                            try:
                                send_to_blynk(temp, hum)
                                mark_as_synced(reading_id)
                                print(" -> Cloud Delivery Sync Success (Live Push completed)")
                            except Exception as e:
                                print(f" -> Direct Cloud sync dropped ({e}). Record safely preserved in cache.")
                        else:
                            print(" -> Link Offline Warning. Stashing data frames inside local cache storage.")

                        # STEP 3: Execute historical queue recovery engine loop sweep
                        resend_unsynced()

                    else:
                        print("[Sensor Exception] Read execution processed, but value context returned None.")

                except RuntimeError:
                    # DHT11 occasionally misses timing frames; isolate and ignore to preserve continuous uptime
                    pass
                except Exception as e:
                    print(f"[Core Exception] Sensor processing framework error: {e}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nShutdown interrupt received. Halting system components smoothly.")

    finally:
        dhtDevice.exit()
