import socket
import json
import random
import time

# ------------------------
# Configuration
# ------------------------
HOST_IP = "127.0.0.1"  # Change if needed
PORT = 5005
BUFFER_SIZE = 4096
TIMEOUT = 0.5
MAX_RETRIES = 3
WAIT_FOR_HOST_DELAY = 6

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
    except (socket.timeout, ConnectionResetError):
        return None, None

# ------------------------
# Host Peer
# ------------------------
def host_peer():
    state = SETUP
    prompt_visible = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, PORT))
    sock.settimeout(TIMEOUT)
    print("Searching for host...")

    try:
        while state == SETUP:
            msg, addr = receive_message(sock)
            if not msg:
                continue

            msg_type = msg.get("message_type")
            if msg_type == "DISCOVER_HOST":
                if not prompt_visible:
                    print("message_type:", end="", flush=True)
                    prompt_visible = True
                response = {"message_type": "DISCOVER_ACK"}
                send_message(sock, addr, response)
            elif msg_type == "HANDSHAKE_REQUEST":
                if not prompt_visible:
                    print("message_type:", end="", flush=True)
                    prompt_visible = True

                seed = random.randint(0, 100000)
                response = {"message_type": "HANDSHAKE_RESPONSE", "seed": seed}
                send_message(sock, addr, response)

                print(" HANDSHAKE_RESPONSE")
                print(f"seed: {seed}")
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

    try:
        # Automatically discover host first
        host_found = False
        attempts = 0
        while attempts < MAX_RETRIES and not host_found:
            send_message(sock, host_addr, {"message_type": "DISCOVER_HOST"})
            msg, addr = receive_message(sock)
            if msg and msg.get("message_type") == "DISCOVER_ACK":
                print("Host Found ...")
                print(f"Host IP : {addr[0]}")
                print(f"Host Broadcast Port: {addr[1]}")
                print(f"({addr[0]}, {addr[1]})")
                host_found = True
                break
            else:
                attempts += 1
                if attempts < MAX_RETRIES:
                    print("(Waiting for Host)")
                    time.sleep(WAIT_FOR_HOST_DELAY)

        if not host_found:
            print("(Waiting for Host)")
            time.sleep(WAIT_FOR_HOST_DELAY)
            print("No active host found. Exiting.")
            return

        # Prompt user once host is confirmed
        while state == SETUP:
            message_type_input = input("message_type:").strip()
            if message_type_input != "HANDSHAKE_REQUEST":
                print("Invalid input\n")
                continue

            send_message(sock, host_addr, {"message_type": message_type_input})

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
                        send_message(sock, host_addr, {"message_type": message_type_input})

            if state != CONNECTED:
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