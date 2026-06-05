import adafruit_dht
import board
import time

# Sensor setup
sensor = adafruit_dht.DHT11(board.D4)

def read_dht11():
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity

        if temperature is not None and humidity is not None:
            return round(temperature, 1), round(humidity, 1)
        else:
            print("Failed to read sensor")
            return None, None

    except RuntimeError as e:
        # DHT sensors are unstable, this is normal
        print("Retrying...", e)
        return None, None


if __name__ == "__main__":
    while True:
        temp, hum = read_dht11()

        if temp is not None:
            print(f"Temperature: {temp}C, Humidity: {hum}%")

        time.sleep(2)
