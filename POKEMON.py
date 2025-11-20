import socket
import json
import random

# ------------------------
# Configuration
# ------------------------
HOST_IP = "127.0.0.1"  # Change to LAN IP if needed
PORT = 5005
BUFFER_SIZE = 4096
TIMEOUT = 0.5  # 500 ms
MAX_RETRIES = 3

# States
SETUP = "SETUP"
CONNECTED = "CONNECTED"

# ------------------------
# UDP Utilities
# ------------------------
def send_message(sock, addr, message):
    sock.sendto(json.dumps(message).encode(), addr)

def receive_message(sock):
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        return json.loads(data.decode()), addr
    except socket.timeout:
        return None, None

# ------------------------
# Host Peer
# ------------------------
def host_peer():
    state = SETUP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, PORT))
    sock.settimeout(TIMEOUT)
    print(f"Host listening on {HOST_IP}:{PORT}")

    try:
        while state == SETUP:
            msg, addr = receive_message(sock)
            if msg is None:
                continue

            msg_type = msg.get("message_type")
            if msg_type in ["HANDSHAKE_REQUEST", "SPECTATOR_REQUEST"]:
                # Generate a seed for player only
                seed = random.randint(0, 100000)
                response = {"message_type": "HANDSHAKE_RESPONSE", "seed": seed}
                send_message(sock, addr, response)

                if msg_type == "HANDSHAKE_REQUEST":
                    random.seed(seed)
                    print(f"Player connected from {addr}, seed {seed} assigned.")
                else:
                    print(f"Spectator connected from {addr}, seed {seed} sent (info only).")

                state = CONNECTED
                print("Host state: CONNECTED")
    finally:
        sock.close()
        print("Host socket closed.")

# ------------------------
# Joiner Peer (Player)
# ------------------------
def joiner_peer(host_ip):
    state = SETUP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    host_addr = (host_ip, PORT)

    handshake_request = {"message_type": "HANDSHAKE_REQUEST"}

    try:
        retries = 0
        while retries < MAX_RETRIES and state == SETUP:
            send_message(sock, host_addr, handshake_request)
            print(f"Sent HANDSHAKE_REQUEST to host ({retries + 1}/{MAX_RETRIES})")

            msg, addr = receive_message(sock)
            if msg and msg.get("message_type") == "HANDSHAKE_RESPONSE":
                seed = msg["seed"]
                random.seed(seed)
                print(f"Received HANDSHAKE_RESPONSE from {addr}, seed {seed}")
                state = CONNECTED
                print("Joiner state: CONNECTED")
                break
            else:
                retries += 1
                print("No response, retrying handshake...")

        if state != CONNECTED:
            print("Failed to handshake with host after maximum retries.")
    finally:
        sock.close()
        print("Joiner socket closed.")

# ------------------------
# Spectator Peer
# ------------------------
def spectator_peer(host_ip):
    state = SETUP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    host_addr = (host_ip, PORT)

    spectator_request = {"message_type": "SPECTATOR_REQUEST"}

    try:
        retries = 0
        while retries < MAX_RETRIES and state == SETUP:
            send_message(sock, host_addr, spectator_request)
            print(f"Sent SPECTATOR_REQUEST to host ({retries + 1}/{MAX_RETRIES})")

            msg, addr = receive_message(sock)
            if msg and msg.get("message_type") == "HANDSHAKE_RESPONSE":
                seed = msg["seed"]
                print(f"Received HANDSHAKE_RESPONSE from host {addr}, seed {seed} (info only)")
                state = CONNECTED
                print("Spectator state: CONNECTED")
                break
            else:
                retries += 1
                print("No response, retrying...")

        if state != CONNECTED:
            print("Failed to connect to host as spectator.")
    finally:
        sock.close()
        print("Spectator socket closed.")

# ------------------------
# Main
# ------------------------
if __name__ == "__main__":
    role = input("Enter your role [Host, Joiner, Spectator]: ").strip().lower()
    if role == "host":
        host_peer()
    elif role == "joiner":
        joiner_peer(HOST_IP)
    elif role == "spectator":
        spectator_peer(HOST_IP)
    else:
        print("Invalid role. Choose Host, Joiner, or Spectator.")