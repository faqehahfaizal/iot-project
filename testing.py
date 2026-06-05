import adafruit_dht
import board
import time

sensor = adafruit_dht.DHT11(board.D4)

while True:
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        print(f"Temp: {temperature}C, Humidity: {humidity}%")

    except RuntimeError as e:
        print("Retrying...", e)

    time.sleep(2)
