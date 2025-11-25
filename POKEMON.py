import socket
import csv
import random
import time
from collections import deque

# ------------------------
# Configuration
# ------------------------
HOST_IP = "172.20.10.3"
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

# Globals
current_seq = 0         # Sequence counter for incoming messages
POKEMON_DATA = None     # Cached CSV


# Buffered incoming messages captured while waiting for ACKs
_pending_messages = deque()

# ------------------------
# UDP UTILITIES
# ------------------------
def send_message(sock, addr, message):
    raw = encode_protocol_message(message)
    sock.sendto(raw, addr)

def receive_message(sock):
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        msg = decode_protocol_message(data)
        return msg, addr
    except (socket.timeout, ConnectionResetError):
        return None, None
    

# ------------------------
# PROTOCOL HELPERS (RFC style)
# ------------------------
def encode_protocol_message(msg_dict):
    # Convert a dict into RFC-style 'key: value' lines, separated by newlines.
    # Example:
    #     {"message_type": "DISCOVER_HOST"} ->
    #     "message_type: DISCOVER_HOST\\n"
    lines = []
    for k, v in msg_dict.items():
        lines.append(f"{k}: {v}")
    text = "\n".join(lines) + "\n"
    return text.encode()  # bytes for sendto()


def decode_protocol_message(raw_bytes):
    # Convert RFC-style 'key: value' lines back into a dict (all values as strings).
    text = raw_bytes.decode()
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


# ------------------------
# RELIABILITY HELPERS
# ------------------------

def get_next_seq():
    global current_seq
    current_seq += 1
    return current_seq

def _buffer_incoming(msg, addr):
    """Store incoming message for later processing."""
    _pending_messages.append((msg, addr))


def _next_incoming(sock):
    """Return buffered message if available, else read from socket."""
    if _pending_messages:
        return _pending_messages.popleft()
    return receive_message(sock)

# ------------------------
# RELIABILITY
# ------------------------
def send_with_retry(sock, addr, message, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    # Add sequence number to message
    seq = get_next_seq()
    message = message.copy()
    message["sequence_number"] = seq

    for attempt in range(max_retries):
        send_message(sock, addr, message)

        start = time.time()
        while time.time() - start < timeout:
            msg, sender = receive_message(sock)
            if not msg:
                continue

            # ACK received
            if msg.get("message_type") == MSG_ACK and seq == msg.get("ack_number", -1):
                return True

            # If the message contains its own sequence_number, ACK it
            if "sequence_number" in msg:
                ack = {"message_type": MSG_ACK, "ack_number": msg["sequence_number"]}
                send_message(sock, sender, ack)

        # retry
    return False

def receive_with_ack(sock):
    msg, addr = receive_message(sock)
    if msg and "sequence_number" in msg:
        ack = {"message_type": MSG_ACK, "ack_number": msg["sequence_number"]}
        send_message(sock, addr, ack)
    return msg, addr
    
# ------------------------
# POKEMON DATA
# ------------------------
def load_pokemon_data(csv_path="pokemon.csv"):
    # TODO: Load Pokemon stats from CSV into a suitable structure.
    # Returns:
    # dict[str, dict]: e.g. data["bulbasaur"] -> {
    #     "name": "Bulbasaur",
    #     "hp": 45,
    #     "attack": 49,
    #     "defense": 49,
    #     "sp_attack": 65,
    #     "sp_defense": 65,
    #     "speed": 45,
    #     "type1": "grass",
    #     "type2": "poison" or None,
    # }
    global POKEMON_DATA 
    data = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue

            def parse_int(key, default=0):
                try:
                    return int(float(row.get(key, default))) # values are strings in the csv and could be returned as "67.0"
                except (ValueError, TypeError):
                    return default
            
            entry = {
                "name": name,
                "hp": parse_int("hp"),
                "attack": parse_int("attack"),
                "defense": parse_int("defense"),
                "sp_attack": parse_int("sp_attack"),
                "sp_defense": parse_int("sp_defense"),
                "speed": parse_int("speed"),
                "type1": (row.get("type1") or "").strip() or None,
                "type2": (row.get("type2") or "").strip() or None,
            }

            data[name.lower()] = entry
    
    POKEMON_DATA = data
    return data


def get_pokemon(name, data):
    # Look up a Pokemon by name
    # return data.get(name)
    if not name:
        return None
    
    # if no data passed, fall back to global cache
    global POKEMON_DATA
    if data is None:
        if POKEMON_DATA is None:
            POKEMON_DATA = load_pokemon_data()
        data = POKEMON_DATA
    
    return data.get(name.strip().lower())
    
# ------------------------
# BATTLE STATE & DAMAGE MODEL SKELETON
# ------------------------
class BattleState:
    # TODO: Represent the full battle state (Pokemon, HP, whose turn, etc.)

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


def host_peer():
    state = SETUP
    prompt_visible = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, PORT))
    sock.settimeout(TIMEOUT)
    print("Searching for host...")

    try:
        while state == SETUP:
            msg, addr = receive_with_ack(sock)
            if not msg:
                continue

            msg_type = msg.get("message_type")

            if msg_type == MSG_DISCOVER_HOST:
                if not prompt_visible:
                    print("message_type:", end="", flush=True)
                    prompt_visible = True

                response = {"message_type": MSG_DISCOVER_ACK}
                send_with_retry(sock, addr, response)

            elif msg_type == MSG_HANDSHAKE_REQUEST:
                if not prompt_visible:
                    print("message_type:", end="", flush=True)
                    prompt_visible = True

                seed = random.randint(0, 100000)
                response = {"message_type": MSG_HANDSHAKE_RESPONSE, "seed": seed}

                send_with_retry(sock, addr, response)

                print(f" {MSG_HANDSHAKE_RESPONSE}")
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
        # Keep trying indefinitely until host responds
        host_found = False
        attempts = 0
        while attempts < MAX_RETRIES and not host_found:
            send_with_retry(sock, host_addr, {"message_type": MSG_DISCOVER_HOST})
            msg, addr = receive_with_ack(sock)

            if msg and msg.get("message_type") == MSG_DISCOVER_ACK:
                print("Host Found ...")
                print(f"Host IP : {addr[0]}")
                print(f"Host Broadcast Port: {addr[1]}")
                print(f"({addr[0]}, {addr[1]})")
                host_found = True
                break

            attempts += 1
            if attempts < MAX_RETRIES:
                print("(Waiting for Host)")
                time.sleep(WAIT_FOR_HOST_DELAY)

        # Handshake
        while state == SETUP:
            user_input = input("message_type: ").strip()
            if user_input != MSG_HANDSHAKE_REQUEST:
                print("Invalid input\n")
                continue

            if send_with_retry(sock, host_addr, {"message_type": MSG_HANDSHAKE_REQUEST}):
                msg, _ = receive_with_ack(sock)
                if msg and msg.get("message_type") == MSG_HANDSHAKE_RESPONSE:
                    seed = int(msg["seed"])
                    random.seed(seed)
                    print("message_type: HANDSHAKE_RESPONSE")
                    print(f"seed: {seed}")
                    state = CONNECTED
                else:
                    print("No response from host, retrying handshake...")
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
    print("Welcome to P2P Pokemon Battle Protocol")
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