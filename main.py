import os
import time
import socket
import struct
from datetime import datetime
import RPi.GPIO as GPIO
from picamera2 import Picamera2

# === Pin definitions (BCM numbering) ===
STEPPER1_DIR = 9
STEPPER1_STEP = 11
STEPPER1_EN = 22

STEPPER2_DIR = 5
STEPPER2_STEP = 6
STEPPER2_EN = 23

BUTTON_PIN = 24
LED_PIN = 17  # PWM capable pin

# === Network info ===
SERVER_IP = '192.168.3.8'  # Windows PC IP
SERVER_PORT = 5000

# === Globals ===
photo_folder = None
photo_count = 0

# Setup GPIO
def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for pin in [STEPPER1_DIR, STEPPER1_STEP, STEPPER1_EN,
                STEPPER2_DIR, STEPPER2_STEP, STEPPER2_EN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    GPIO.output(STEPPER1_EN, GPIO.LOW)
    GPIO.output(STEPPER2_EN, GPIO.LOW)

    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(LED_PIN, GPIO.OUT)
    global led_pwm
    led_pwm = GPIO.PWM(LED_PIN, 1000)
    led_pwm.start(0)

def led_set_brightness(percent):
    led_pwm.ChangeDutyCycle(max(0, min(100, percent)))

# Setup camera with macro autofocus
def setup_camera():
    global picam2
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()

    try:
        controls = picam2.camera_controls
        if 'AfMode' in controls:
            picam2.set_controls({"AfMode": 1})  # Enable autofocus
        if 'AfRange' in controls:
            picam2.set_controls({"AfRange": 2})  # Macro mode for close objects
        if 'LensPosition' in controls:
            picam2.set_controls({"LensPosition": 1.5})  # Close focus tuning
        print("Macro autofocus enabled")
    except Exception as e:
        print(f"Warning: Macro autofocus failed: {e}")

    time.sleep(2)

# Create photo folder with timestamp
def create_photo_folder():
    global photo_folder
    timestamp = datetime.now().strftime("%M_%H_%d_%m_%Y")
    photo_folder = os.path.join(os.getcwd(), f"Photos_{timestamp}")
    os.makedirs(photo_folder, exist_ok=True)
    print(f"Created photo folder: {photo_folder}")

# Take photo with macro autofocus
def take_photo():
    global photo_count
    photo_count += 1
    filename = f"Photo_{photo_count}.jpg"
    filepath = os.path.join(photo_folder, filename)

    try:
        picam2.set_controls({"AfTrigger": 0})
        picam2.set_controls({"AfRange": 2})  
        picam2.set_controls({"LensPosition": 1.5})  
        time.sleep(2)
    except Exception as e:
        print(f"Autofocus trigger failed: {e}")

    picam2.capture_file(filepath)
    print(f"Captured {filename}")
    time.sleep(1)

# Stepper movement functions
def move_stepper(step_pin, dir_pin, enable_pin, direction, rpm, revolutions):
    GPIO.output(enable_pin, GPIO.LOW)
    GPIO.output(dir_pin, GPIO.HIGH if direction in ['up', 'right'] else GPIO.LOW)

    steps_per_revolution = 200
    delay = 60.0 / (steps_per_revolution * rpm)
    total_steps = int(steps_per_revolution * revolutions)

    for _ in range(total_steps):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay / 2)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay / 2)

    GPIO.output(enable_pin, GPIO.HIGH)

def move_stepper1(direction, rpm, revolutions):
    move_stepper(STEPPER1_STEP, STEPPER1_DIR, STEPPER1_EN, direction, rpm, revolutions)

def move_stepper2(direction, rpm, revolutions):
    move_stepper(STEPPER2_STEP, STEPPER2_DIR, STEPPER2_EN, direction, rpm, revolutions)

# Home Stepper1 by moving down until button press
def move_stepper1_down_until_button(rpm):
    GPIO.output(STEPPER1_EN, GPIO.LOW)
    GPIO.output(STEPPER1_DIR, GPIO.LOW)
    
    steps_per_revolution = 200
    delay = 60.0 / (steps_per_revolution * rpm)

    print("Moving Stepper1 down until button press...")
    while GPIO.input(BUTTON_PIN):
        GPIO.output(STEPPER1_STEP, GPIO.HIGH)
        time.sleep(delay / 2)
        GPIO.output(STEPPER1_STEP, GPIO.LOW)
        time.sleep(delay / 2)
    print("Stepper1 homed")
    GPIO.output(STEPPER1_EN, GPIO.HIGH)

# Send folder with photos via TCP
def send_folder_via_tcp(folder_path, server_ip, server_port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")

        for root, _, files in os.walk(folder_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                filesize = os.path.getsize(filepath)
                print(f"Sending {filename} ({filesize} bytes)")

                fname_bytes = filename.encode()
                s.sendall(struct.pack('<I', len(fname_bytes)))
                s.sendall(fname_bytes)
                s.sendall(struct.pack('<Q', filesize))

                with open(filepath, 'rb') as f:
                    while chunk := f.read(4096):
                        s.sendall(chunk)
                print(f"Sent {filename}")

        s.sendall(struct.pack('<I', 0))
        print("All files sent.")
    except Exception as e:
        print(f"Error sending files: {e}")
    finally:
        s.close()

# Main process
def main():
    gpio_setup()
    setup_camera()
    create_photo_folder()
    led_set_brightness(50)

    try:
        move_stepper1_down_until_button(rpm=300)
        move_stepper1('up', rpm=300, revolutions=70)

        current_height = 70
        while current_height > 0:
            total_rot_2 = 0
            while total_rot_2 < 16:
                move_stepper2('right', rpm=120, revolutions=4)
                time.sleep(2)
                take_photo()
                total_rot_2 += 4

            move_stepper1('down', rpm=200, revolutions=10)
            current_height -= 10

            if current_height <= 0 or GPIO.input(BUTTON_PIN) == GPIO.LOW:
                while total_rot_2 < 16:
                    move_stepper2('right', rpm=120, revolutions=4)
                    time.sleep(2)
                    take_photo()
                    total_rot_2 += 4
                break

        print("Stepper1 reached bottom")

        total_rot_2 = 0
        while total_rot_2 < 16:
            move_stepper2('right', rpm=120, revolutions=4)
            time.sleep(2)
            take_photo()
            total_rot_2 += 4

        print("Scan complete, sending photos to PC...")
        send_folder_via_tcp(photo_folder, SERVER_IP, SERVER_PORT)

    finally:
        led_set_brightness(0)
        led_pwm.stop()
        GPIO.cleanup()
        picam2.close()
        print("Cleanup done, exiting.")

if __name__ == "__main__":
    main()
