import socket
import json
import random
import time
from collections import deque
import csv

#LAST CODE WITH INA NUNG MONDAY GOKS (PENDING PROGRESS BATTLE_SETUP)
# ------------------------
# Configuration
# ------------------------
HOST_IP = "10.159.62.24"
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
MSG_BATTLE_SETUP = "BATTLE_SETUP"

# Buffered incoming messages captured while waiting for ACKs
_pending_messages = deque()
POKEMON_DATA = {}

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
    lines = []
    for k, v in msg_dict.items():
        lines.append(f"{k}: {v}")
    text = "\n".join(lines) + "\n"
    return text.encode()

def decode_protocol_message(raw_bytes):
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
current_seq = 0  # Global sequence counter for outgoing messages

def get_next_seq():
    global current_seq
    current_seq += 1
    return current_seq

def _buffer_incoming(msg, addr):
    _pending_messages.append((msg, addr))

def _next_incoming(sock):
    if _pending_messages:
        return _pending_messages.popleft()
    return receive_message(sock)

# ------------------------
# RELIABILITY
# ------------------------
def send_with_retry(sock, addr, message, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    # Add sequence number to message
    seq = random.randint(1, 9999999)
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
            if msg.get("message_type") == MSG_ACK and str(seq) == msg.get("ack_number"):
                return True

            # If the message contains its own sequence_number, ACK it
            if "sequence_number" in msg:
                ack = {"message_type": MSG_ACK, "ack_number": msg["sequence_number"]}
                send_message(sock, sender, ack)

        # retry
    print(f"[ERROR] No ACK for seq {seq} after {max_retries} retries.")
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
    data = {}
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                if not name:
                    continue
                data[name.lower()] = row
    except FileNotFoundError:
        print("[ERROR] pokemon.csv not found in current directory.")
    return data

def get_pokemon(name, data):
    if not name:
        return None
    return data.get(name.lower())

def build_pokemon_battle_data(row):
    def as_int(key, default=0):
        try:
            return int(float(row.get(key, default)))
        except ValueError:
            return default
    return {
        "name": row.get("name", ""),
        "hp": as_int("hp"),
        "attack": as_int("attack"),
        "defense": as_int("defense"),
        "sp_attack": as_int("sp_attack"),
        "sp_defense": as_int("sp_defense"),
        "speed": as_int("speed"),
        "type1": row.get("type1", ""),
        "type2": row.get("type2", "") or "",
        "pokedex_number": as_int("pokedex_number")
    }
    
# ------------------------
# BATTLE STATE & DAMAGE MODEL SKELETON
# ------------------------
class BattleState:
    def __init__(self):
        self.example = None
        self.state = SETUP
        self.self_pokemon = None
        self.opponent_pokemon = None
        self.self_boosts = None
        self.opponent_boosts = None

    def is_game_over(self):
        return False


def calculate_damage(attacker_stats, defender_stats, move_info):
    pass

# ------------------------
# TURN FLOW SKELETON
# ------------------------
def run_turn_as_attacker(sock, peer_addr, battle_state):
    pass

def run_turn_as_defender(sock, peer_addr, battle_state):
    pass


# ------------------------
# CHAT SKELETON: Text + Stickers
# ------------------------
def send_chat_message(sock, addr, text=None, sticker_b64=None):
    pass

def handle_incoming_chat(msg):
    pass

# ------------------------
# BATTLE SETUP PHASE (4.4)
# ------------------------
def battle_setup_phase(sock, peer_addr, battle_state):
    global POKEMON_DATA
    while True:
        name = input("Enter your Pokémon name: ").strip()
        row = get_pokemon(name, POKEMON_DATA)
        if row:
            break
        print("Pokémon not found in CSV, try again.")

    self_pokemon = build_pokemon_battle_data(row)
    self_boosts = {"special_attack_uses": 5, "special_defense_uses": 5}
    battle_state.self_pokemon = self_pokemon
    battle_state.self_boosts = self_boosts

    msg = {
        "message_type": MSG_BATTLE_SETUP,
        "communication_mode": "P2P",
        "pokemon_name": self_pokemon["name"],
        "stat_boosts": json.dumps(self_boosts),
        "pokemon": json.dumps(self_pokemon)
    }

    if not send_with_retry(sock, peer_addr, msg):
        print("[ERROR] Failed to send BATTLE_SETUP.")
        return False

    print("Sent BATTLE_SETUP. Waiting for opponent setup...")

    while True:
        incoming, addr = receive_with_ack(sock)
        if not incoming:
            continue
        if incoming.get("message_type") == MSG_BATTLE_SETUP:
            try:
                opp_name = incoming["pokemon_name"]
                opp_pokemon = json.loads(incoming["pokemon"])
                opp_boosts = json.loads(incoming["stat_boosts"])
            except (KeyError, json.JSONDecodeError):
                print("[ERROR] Invalid BATTLE_SETUP received, waiting again...")
                continue

            battle_state.opponent_pokemon = opp_pokemon
            battle_state.opponent_boosts = opp_boosts
            print(f"Opponent selected: {opp_name}")
            return True

# ------------------------
# HOST / JOINER / SPECTATOR
# ------------------------
def host_peer():
    state = SETUP
    prompt_visible = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, PORT))
    sock.settimeout(TIMEOUT)
    battle_state = BattleState()
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
                state = BATTLE_SETUP
                battle_state.state = BATTLE_SETUP

                if not battle_setup_phase(sock, addr, battle_state):
                    return

                print("Battle setup complete. Waiting for move...")
                battle_state.state = WAITING_FOR_MOVE
                state = WAITING_FOR_MOVE
                return
    finally:
        sock.close()
        print("Host socket closed.")

def joiner_peer(host_ip):
    state = SETUP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    host_addr = (host_ip, PORT)
    battle_state = BattleState()
    print("Searching for host...")

    try:
        # Keep trying until host responds (bounded by MAX_RETRIES)
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
                    state = BATTLE_SETUP
                    battle_state.state = BATTLE_SETUP

                    if not battle_setup_phase(sock, host_addr, battle_state):
                        return

                    print("Battle setup complete. Waiting for move...")
                    battle_state.state = WAITING_FOR_MOVE
                    state = WAITING_FOR_MOVE
                    return
                else:
                    print("No response from host, retrying handshake...")
    finally:
        sock.close()
        print("Joiner socket closed.")

def spectator_peer(host_ip):
    print("Spectator mode is not yet implemented.")

# ------------------------
# MAIN WRAPPER & ENTRY POINT
# ------------------------
def main():
    global POKEMON_DATA
    POKEMON_DATA = load_pokemon_data()
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
            spectator_peer(HOST_IP)
            break
        else:
            print("Invalid role. Choose Host, Joiner, or Spectator.\n")

if __name__ == "__main__":
    main()