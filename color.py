import subprocess
import cv2
import numpy as np
import RPi.GPIO as GPIO
from time import sleep

# GPIO Pin Definitions
red_pin = 17   # GPIO pin for red valve
green_pin = 27 # GPIO pin for green valve
blue_pin = 22  # GPIO pin for blue valve
motor_pin = 23 # GPIO pin for motor

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)
GPIO.setup(motor_pin, GPIO.OUT)

def capture_image(image_path="captured_image.jpg"):
    try:
        # Run the libcamera-still command to capture an image
        subprocess.run(["libcamera-still", "-o", image_path], check=True)
        print(f"Image captured and saved to {image_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while capturing the image: {e}")

def get_dominant_color(image_path, k=4):
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not open or find the image at {image_path}.")
        return None

    # Reshape the image to a 2D array of pixels
    pixels = image.reshape((-1, 3))

    # Convert to float type for k-means
    pixels = np.float32(pixels)

    # Define criteria and apply k-means clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, palette = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # Count the number of pixels in each cluster
    _, counts = np.unique(labels, return_counts=True)

    # Get the dominant color
    dominant_color = palette[np.argmax(counts)]

    # Convert to integer type
    dominant_color = dominant_color.astype(int)

    return tuple(dominant_color)

def normalize_rgb(r, g, b):
    return r / 255, g / 255, b / 255

def calculate_valve_times(normalized_rgb, base_time_s):
    r_normalized, g_normalized, b_normalized = normalized_rgb
    
    red_time = r_normalized * base_time_s
    green_time = g_normalized * base_time_s
    blue_time = b_normalized * base_time_s
    motor_time = red_time + green_time + blue_time
    
    return red_time, green_time, blue_time, motor_time

def open_valve(pin, duration, color_name):
    print(f"Opening {color_name} valve for {duration:.2f} seconds...")
    GPIO.output(pin, GPIO.HIGH)
    sleep(duration)
    GPIO.output(pin, GPIO.LOW)
    print(f"Closing {color_name} valve.")

def main():
    image_path = "captured_image.jpg"
    
    # Capture image
    capture_image(image_path)

    # Get the dominant color
    dominant_color = get_dominant_color(image_path)
    if dominant_color:
        print(f"Dominant Color (RGB): {dominant_color}")

        # Normalize the RGB values
        normalized_rgb = normalize_rgb(*dominant_color)
        print(f"Normalized RGB: {normalized_rgb}")

        # Base time in seconds
        base_time_s = 5

        # Calculate the valve times
        red_time, green_time, blue_time, motor_time = calculate_valve_times(normalized_rgb, base_time_s)
        print(f"Valve times: Red={red_time:.2f} seconds, Green={green_time:.2f} seconds, Blue={blue_time:.2f} seconds, Motor={motor_time:.2f} seconds")

        # Open valves sequentially
        open_valve(red_pin, red_time, "red")
        sleep(1)  # wait for 1 second

        open_valve(green_pin, green_time, "green")
        sleep(1)  # wait for 1 second

        open_valve(blue_pin, blue_time, "blue")
        sleep(1)  # wait for 1 second

        # Open motor for the calculated motor time
        open_valve(motor_pin, motor_time, "motor")

    # Cleanup GPIO
    GPIO.cleanup()

if __name__ == "__main__":
    main()
