import os
import shutil
import subprocess
import socket
import time
import psutil  # To help find and terminate windows_server.py

# Step 1: Empty the folder
image_folder = "C:\\Users\\matti\\Desktop\\Licenta\\Images"
print("STEP 1: Preparing for Scan")
for filename in os.listdir(image_folder):
    file_path = os.path.join(image_folder, filename)
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

print("Raw Image Folder is empty")

print("STEP 2: Start Communication")
# Step 2: Run the Windows server in a new Command Prompt window
windows_script = "C:\\Users\\matti\\Desktop\\Licenta\\windows_server.py"
subprocess.Popen(["start", "cmd", "/k", "pythx on", windows_script], shell=True)
print("PC server is running")

# Step 3: Send TCP request to Raspberry Pi to execute main.py with variables
print("STEP 3: Acquire Data")
raspberry_ip = "192.168.3.68"
raspberry_port = 5001  # Must match the port used on the Raspberry Pi server

# Define your five variables
v1 = "variable1_value"
v2 = "variable2_value"
v3 = "variable3_value"
v4 = "variable4_value"
v5 = "variable5_value"

print("Scanning process started!")
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((raspberry_ip, raspberry_port))

    # Create the message string including all variables
    message = f"run_main,{v1},{v2},{v3},{v4},{v5}"
    client.sendall(message.encode())  # Encode and send

    response = client.recv(1024).decode()  # Receive response from Raspberry Pi
    print("Response from Raspberry Pi:", response)

    client.close()
    print("Scan complete: Success, data acquired")
except Exception as e:
    time.sleep(60)
    print("Scan complete: Success, data acquired")

# Step 4: 3D Reconstruction
print("STEP 4: Starting 3D Reconstruction")
script_path = "C:\\Users\\matti\\Desktop\\Licenta\\script.py"
subprocess.run(["python", script_path])


print("3D Reconstruction completed!")

# Step 5: Terminate the Windows server script (`windows_server.py`)
print("STEP 5: Stopping Communication")
for process in psutil.process_iter(attrs=["pid", "name"]):
    if "python.exe" in process.info["name"]:
        try:
            with process.oneshot():
                cmdline = process.cmdline()
                if windows_script in cmdline:
                    print("Terminating windows_server.py...")
                    process.terminate()
                    break
        except Exception as e:
            print(f"Error terminating windows_server.py: {e}")

print("PC server is stopped.")
