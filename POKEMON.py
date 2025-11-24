import socket
import json
import random

# ------------------------
# Configuration
# ------------------------
HOST_IP = "127.0.0.1"  # Change if needed
PORT = 5005
BUFFER_SIZE = 4096
TIMEOUT = 0.5
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
    print("Searching for host...")

    try:
        while state == SETUP:
            msg, addr = receive_message(sock)
            if msg and msg.get("message_type") == "HANDSHAKE_REQUEST":
                print("message_type:", end="", flush=True)
                seed = random.randint(0, 100000)
                response = {"message_type": "HANDSHAKE_RESPONSE", "seed": seed}
                send_message(sock, addr, response)

                print(" HANDSHAKE_RESPONSE")
                print(f"seed: {seed}")
                print("message_type:")
                random.seed(seed)
                state = CONNECTED
    finally:
        sock.close()
        print("Host socket closed.")

# ------------------------
# Joiner Peer
# ------------------------
def joiner_peer(host_ip):
    state = SETUP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    host_addr = (host_ip, PORT)

    print("Searching for host...")

    # Display host info immediately (we assume host IP/port is known)
    print("Host Found ...")
    print(f"Host IP : {host_addr[0]}")
    print(f"Host Broadcast Port: {host_addr[1]}")
    print(f"({host_addr[0]}, {host_addr[1]})")

    try:
        while state == SETUP:
            message_type_input = input("message_type:").strip()
            if message_type_input != "HANDSHAKE_REQUEST":
                print("Invalid input\n")
                continue

            # Send handshake request to host
            send_message(sock, host_addr, {"message_type": message_type_input})

            # Wait for host response with retries
            retries = 0
            while retries < MAX_RETRIES:
                msg, _ = receive_message(sock)
                if msg and msg.get("message_type") == "HANDSHAKE_RESPONSE":
                    seed = msg["seed"]
                    random.seed(seed)

                    print("message_type: HANDSHAKE_RESPONSE")
                    print(f"seed: {seed}")
                    state = CONNECTED
                    break
                else:
                    retries += 1
                    if retries < MAX_RETRIES:
                        # Resend the request
                        send_message(sock, host_addr, {"message_type": message_type_input})
            
            if state == CONNECTED:
                break
            else:
                print("No response from host, try again.")

    finally:
        sock.close()
        print("Joiner socket closed.")

# ------------------------
# Main
# ------------------------
if __name__ == "__main__":
    print("Welcome to P2P Pokémon Battle Protocol")
    while True:
        role = input("Enter your role [Host, Joiner, Spectator]: ").strip().lower()
        if role == "host":
            host_peer()
            break
        elif role == "joiner":
            joiner_peer(HOST_IP)
            break
        elif role == "spectator":
            pass  # leave empty for now
            break
        else:
            print("Invalid role. Choose Host, Joiner, or Spectator.\n")