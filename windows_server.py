import socket
import struct
import os

SAVE_DIR = r"C:\Users\matti\Desktop\Licenta\Images"
os.makedirs(SAVE_DIR, exist_ok=True)

SERVER_IP = '0.0.0.0'  
SERVER_PORT = 5000

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((SERVER_IP, SERVER_PORT))
        s.listen(1)
        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            with conn:
                while True:
                    raw_fname_len = recvall(conn, 4)
                    if not raw_fname_len:
                        break
                    fname_len = struct.unpack('<I', raw_fname_len)[0]
                    if fname_len == 0:
                        print("File transfer complete.")
                        break
                    filename = recvall(conn, fname_len).decode()
                    raw_filesize = recvall(conn, 8)
                    filesize = struct.unpack('<Q', raw_filesize)[0]

                    filepath = os.path.join(SAVE_DIR, filename)
                    print(f"Receiving {filename} ({filesize} bytes)")

                    with open(filepath, 'wb') as f:
                        remaining = filesize
                        while remaining > 0:
                            chunk_size = 4096 if remaining >= 4096 else remaining
                            chunk = conn.recv(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            remaining -= len(chunk)
                    print(f"Saved {filepath}")
            print("Connection closed")

if __name__ == "__main__":
    start_server()
