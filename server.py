import socket
import subprocess

HOST = "0.0.0.0"  # Raspberry Pi's IP
PORT = 5001       # Choose an available port

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Waiting for connection...")

while True:
    conn, addr = server.accept()
    print(f"Connected by {addr}")
    
    data = conn.recv(1024).decode()
    
    # Split received data into command and variables
    values = data.split(",")  # Expected format: "run_main,v1,v2,v3,v4,v5"

    if values[0] == "run_main":  # Ensure it's the correct command
        v1, v2, v3, v4, v5 = values[1:]  # Extract variables
        print(f"Executing main.py with variables: {v1}, {v2}, {v3}, {v4}, {v5}")

        # Pass variables to main.py via subprocess
        subprocess.run(["python3", "/home/3dscanner/Documents/main.py", v1, v2, v3, v4, v5])

        conn.sendall(b"Script executed successfully with received variables")

    conn.close()

