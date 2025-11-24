import socket
import json
import random
import time

# ------------------------
# Configuration
# ------------------------
HOST_IP = "127.0.0.1"
PORT = 5005
BUFFER_SIZE = 4096
TIMEOUT = 0.5
MAX_RETRIES = 3
WAIT_FOR_HOST_DELAY = 6

# States
SETUP = "SETUP"
CONNECTED = "CONNECTED"
BATTLE_SETUP = "BATTLE_SETUP"
WAITING_FOR_MOVE = "WAITING_FOR_MOVE"
PROCESSING_TURN = "PROCESSING_TURN"
GAME_OVER = "GAME_OVER"

# Message Type Constants (Based on RFC)
MSG_DISCOVER_HOST = "DISCOVER_HOST"
MSG_DISCOVER_ACK = "DISCOVER_ACK"
MSG_HANDSHAKE_REQUEST = "HANDSHAKE_REQUEST"
MSG_HANDSHAKE_RESPONSE = "HANDSHAKE_RESPONSE"
MSG_ATTACK_ANNOUNCE = "ATTACK_ANNOUNCE"
MSG_DEFENSE_ANNOUNCE = "DEFENSE_ANNOUNCE"
MSG_CALCULATION_REPORT = "CALCULATION_REPORT"
MSG_CALCULATION_CONFIRM = "CALCULATION_CONFIRM"
MSG_RESOLUTION_REQUEST = "RESOLUTION_REQUEST"
MSG_GAME_OVER = "GAME_OVER"
MSG_CHAT = "CHAT_MESSAGE"
MSG_ACK = "ACK"

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
# PROTOCOL HELPERS (RFC style)
# ------------------------


# ------------------------
# RELIABILITY
# ------------------------
def send_with_retry(sock, addr, message, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    # TODO: Wrap send_message() with ACK/timeout handling.
    # Currently discovery and handshake in host_peer() and joiner_peer() do their
    # own retry logic so this isn't needed at all, but it would be worth abstracting
    # logic moving forward

    send_message(sock, addr, message) # stub
    return True
    
# ------------------------
# POKEMON DATA
# ------------------------
def load_pokemon_data(csv_path="pokemon.csv"):
    # TODO: Load Pokémon stats from CSV into a suitable structure.
    # Implementation choice, not a hard written requirement as per RFC
    # Whil RFC does not say anything about where data comes from explicitly,
    # in practice especially for testing the CSV is the best resource for data
    pass


def get_pokemon(name, data):
    # TODO: Fetch a single Pokémon's stats from loaded data.
    # return data.get(name)
    pass
    
# ------------------------
# BATTLE STATE & DAMAGE MODEL SKELETON
# ------------------------
class BattleState:
    # TODO: Represent the full battle state (Pokémon, HP, whose turn, etc.)

    def __init__(self):
        # placeholder attribute/s
        # fill in later (e.g. host_poke, joiner_probe, hp, etc.)
        self.example = None

    def is_game_over(self):
        # TODO: Return True/False and winner info.
        return False


def calculate_damage(attacker_stats, defender_stats, move_info):
    # TODO: Implement damage as per RFC
    pass

# ------------------------
# TURN FLOW SKELETON
# ------------------------
def run_turn_as_attacker(sock, peer_addr, battle_state):
    # TODO: Implement the 4-step turn as attacker:
    #     1. ATTACK_ANNOUNCE
    #     2. DEFENSE_ANNOUNCE
    #     3. CALCULATION_REPORT
    #     4. CALCULATION_CONFIRM / RESOLUTION_REQUEST
    pass


def run_turn_as_defender(sock, peer_addr, battle_state):
    # TODO: Implement the 4-step turn as defender
    pass


# ------------------------
# CHAT SKELETON: Text + Stickers
# ------------------------
def send_chat_message(sock, addr, text=None, sticker_b64=None):
    # TODO: Implement chat messages on top of the protocol
    pass

def handle_incoming_chat(msg):
    # TODO: Handle and display incoming chat message (text/sticker)
    pass


# ------------------------
# ROLE LOGIC: Host / Joiner / Spectator
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

def spectator_peer(host_ip):
    # TODO: Implement
    # Temporary placeholder so spectator in main cleanly exits
    print("Spectator mode is not yet implemented.")

# ------------------------
# MAIN WRAPPER & ENTRY POINT
# ------------------------
def main():
    print("Welcome to P2P Pokémon Battle Protocol")
    while True:
        role = input("Enter your role [Host, Joiner, Spectator]: ").strip().lower()
        if role == "host":
            host_peer()
            break
        elif role == "joiner":
            joiner_peer(HOST_IP) # Temporary (?)
            break
        elif role == "spectator":
            # spectator_peer(HOST_IP)
            pass  # leave empty for now
            break
        else:
            print("Invalid role. Choose Host, Joiner, or Spectator.\n")

if __name__ == "__main__":
    main()