import socket
import threading
import json
import time
import sys
import os
import base64
import random
import pandas as pd
from PIL import Image 

POKE_RED = "\033[38;2;255;75;75m"
POKE_BLUE = "\033[38;2;56;126;255m"
POKE_YELLOW = "\033[38;2;255;222;89m"
POKE_GOLD = "\033[38;2;212;175;55m"
POKE_GREEN = "\033[38;2;100;220;150m"
POKE_PURPLE = "\033[38;2;180;100;255m"
POKE_GRAY = "\033[38;2;170;170;170m"
POKE_ORANGE = "\033[38;2;255;140;0m"
POKE_PINK = "\033[38;2;255;105;180m"

BG_DARK = "\033[48;2;15;15;30m"
BG_PANEL = "\033[48;2;25;25;45m"
BG_ALERT = "\033[48;2;60;0;0m"

BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDER = "\033[4m"
RESET = "\033[0m"

PORT = 5432
BROADCAST_PORT = 5217
BUFFER_SIZE = 4096
MAX_RETRIES = 3
MAX_SP_USES = 5
SESSION_ACTIVE = True
BROADCAST_ACTIVE = True

broadcast_sock = None

pokemon_df = None
peer_addr = None
my_role = None
my_name = None
battle_state = None
my_pokemon = None
opponent_pokemon = None
my_data = None
opponent_data = None
comm_mode = None
last_move_name = None
last_opponent_move = None
next_attacker = None

damage_result = None

spectator_count = 0
spectators = []

res_count = 0
sp_count = 0
seq = 0
ack_received = None

BORDER = f"{POKE_ORANGE}{BOLD}======================================================================={RESET}"
BGOLD = f"{POKE_GOLD}{BOLD}======================================================================={RESET}"
BPINK = f"{POKE_PINK}{BOLD}======================================================================={RESET}"
BBLUE = f"{POKE_BLUE}{BOLD}======================================================================={RESET}"
BRED = f"{POKE_RED}{BOLD}======================================================================={RESET}"
BGREEN = f"{POKE_GREEN}{BOLD}======================================================================={RESET}"
BPURP = f"{POKE_PURPLE}{BOLD}======================================================================={RESET}"
BYELLOW = f"{POKE_YELLOW}{BOLD}======================================================================={RESET}"

pokemon_moves = [
    {"name": "Flare Blitz", "category": "Physical", "type": "Fire", "power": 60},
    {"name": "Blaze Kick", "category": "Physical", "type": "Fire", "power": 42},
    {"name": "Flamethrower", "category": "Special", "type": "Fire", "power": 45},
    {"name": "Waterfall", "category": "Physical", "type": "Water", "power": 40},
    {"name": "Aqua Jet", "category": "Physical", "type": "Water", "power": 20},
    {"name": "Surf", "category": "Special", "type": "Water", "power": 45},
    {"name": "Wild Charge", "category": "Physical", "type": "Electric", "power": 45},
    {"name": "Thunder Punch", "category": "Physical", "type": "Electric", "power": 37},
    {"name": "Thunderbolt", "category": "Special", "type": "Electric", "power": 45},
    {"name": "Leaf Blade", "category": "Physical", "type": "Grass", "power": 45},
    {"name": "Power Whip", "category": "Physical", "type": "Grass", "power": 60},
    {"name": "Energy Ball", "category": "Special", "type": "Grass", "power": 45},
    {"name": "Ice Punch", "category": "Physical", "type": "Ice", "power": 37},
    {"name": "Ice Shard", "category": "Physical", "type": "Ice", "power": 20},
    {"name": "Ice Beam", "category": "Special", "type": "Ice", "power": 45},
    {"name": "Earthquake", "category": "Physical", "type": "Ground", "power": 50},
    {"name": "Dig", "category": "Physical", "type": "Ground", "power": 40},
    {"name": "Earth Power", "category": "Special", "type": "Ground", "power": 45},
    {"name": "Rock Slide", "category": "Physical", "type": "Rock", "power": 37},
    {"name": "Rock Blast", "category": "Physical", "type": "Rock", "power": 12},
    {"name": "Power Gem", "category": "Special", "type": "Rock", "power": 40},
    {"name": "Brave Bird", "category": "Physical", "type": "Flying", "power": 60},
    {"name": "Acrobatics", "category": "Physical", "type": "Flying", "power": 27},
    {"name": "Air Slash", "category": "Special", "type": "Flying", "power": 37},
    {"name": "U-turn", "category": "Physical", "type": "Bug", "power": 35},
    {"name": "Megahorn", "category": "Physical", "type": "Bug", "power": 60},
    {"name": "Bug Buzz", "category": "Special", "type": "Bug", "power": 45},
    {"name": "Poison Jab", "category": "Physical", "type": "Poison", "power": 40},
    {"name": "Gunk Shot", "category": "Physical", "type": "Poison", "power": 60},
    {"name": "Sludge Bomb", "category": "Special", "type": "Poison", "power": 45},
    {"name": "Zen Headbutt", "category": "Physical", "type": "Psychic", "power": 40},
    {"name": "Psycho Cut", "category": "Physical", "type": "Psychic", "power": 35},
    {"name": "Psychic", "category": "Special", "type": "Psychic", "power": 45},
    {"name": "Shadow Claw", "category": "Physical", "type": "Ghost", "power": 35},
    {"name": "Shadow Sneak", "category": "Physical", "type": "Ghost", "power": 20},
    {"name": "Shadow Ball", "category": "Special", "type": "Ghost", "power": 40},
    {"name": "Dragon Claw", "category": "Physical", "type": "Dragon", "power": 40},
    {"name": "Outrage", "category": "Physical", "type": "Dragon", "power": 60},
    {"name": "Draco Meteor", "category": "Special", "type": "Dragon", "power": 65},
    {"name": "Sucker Punch", "category": "Physical", "type": "Dark", "power": 35},
    {"name": "Knock Off", "category": "Physical", "type": "Dark", "power": 32},
    {"name": "Dark Pulse", "category": "Special", "type": "Dark", "power": 40},
    {"name": "Iron Head", "category": "Physical", "type": "Steel", "power": 40},
    {"name": "Bullet Punch", "category": "Physical", "type": "Steel", "power": 20},
    {"name": "Flash Cannon", "category": "Special", "type": "Steel", "power": 40},
    {"name": "Play Rough", "category": "Physical", "type": "Fairy", "power": 45},
    {"name": "Spirit Break", "category": "Physical", "type": "Fairy", "power": 37},
    {"name": "Moonblast", "category": "Special", "type": "Fairy", "power": 47},
    {"name": "Close Combat", "category": "Physical", "type": "Fighting", "power": 60},
    {"name": "Brick Break", "category": "Physical", "type": "Fighting", "power": 37},
    {"name": "Aura Sphere", "category": "Special", "type": "Fighting", "power": 40},
    {"name": "Body Slam", "category": "Physical", "type": "Normal", "power": 42},
    {"name": "Return", "category": "Physical", "type": "Normal", "power": 51},
    {"name": "Hyper Voice", "category": "Special", "type": "Normal", "power": 45},
]

def clear_line():
    sys.stdout.write('\r\033[K')
    sys.stdout.flush()

def title_banner():
    print(BG_DARK + POKE_GOLD + BOLD)
    print(r"""
        ______     _       ______          _                  _ 
        | ___ \   | |      | ___ \        | |                | |
        | |_/ /__ | | _____| |_/ / __ ___ | |_ ___   ___ ___ | |
        |  __/ _ \| |/ / _ \  __/ '__/ _ \| __/ _ \ / __/ _ \| |
        | | | (_) |   <  __/ |  | | | (_) | || (_) | (_| (_) | |
        \_|  \___/|_|\_\___\_|  |_|  \___/ \__\___/ \___\___/|_|
""")
    print(f"{RESET}")
    print(f"{POKE_RED}{BOLD}                Welcome to P2P Pokémon Battle Protocol {RESET}")
    print()

def prompt_label(label):
    return f"{label}{RESET} "

def info_message(text, color=POKE_BLUE):
    clear_line()
    print(f"{color}{BOLD}{text}{RESET}")

def success_message(text):
    clear_line()
    print(f"{POKE_GREEN}{BOLD}{text}{RESET}")

def error_message(text):
    clear_line()
    print(f"{BG_ALERT}{POKE_RED}{BOLD}{text}{RESET}")

def system_message(text, color=POKE_YELLOW):
    clear_line()
    print(f"{BG_PANEL}{color}{BOLD}{text}{RESET}")

def welcome_message():
    global my_role
    title_banner()
    print(f"{BORDER}")
    title = "ROLE SELECTION"
    inner_width = 70  
    centered_title = title.center(inner_width)
    centered_title = " " + centered_title.rstrip()  
    print(f"{BOLD}{centered_title}{RESET}")
    print(f"{BORDER}")
    print(f"  Choose your role:{RESET}")
    print(f"  {POKE_BLUE}{BOLD}[Host]{RESET}{POKE_BLUE} -> Create a lobby and wait for Joiner.{RESET}")
    print(f"  {POKE_YELLOW}{BOLD}[Peer]{RESET}{POKE_YELLOW}  -> Join a Host to battle.{RESET}")
    print(f"  {POKE_RED}{BOLD}[Spectator]{RESET}{POKE_RED}  -> Spectate a Battle.{RESET}")
    print(f"{BORDER}")
  
    while my_role is None:
        role = input(prompt_label("  Enter role [Host/Peer/Spectator]:")).strip().title()
        
        if role in ["Host", "Peer", "Spectator"]:
            my_role = role
        
def create_socket():
    global my_socket, my_name
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if my_role == "Host":
        my_socket.bind(('', PORT))
        my_name = "Player1"
        success_message("  Host socket initialized, Waiting for Joiners...") 
    else:
        my_socket.bind(('', 0))
        if my_role == "Peer":
            my_name = "Player2"
        else:
            my_name = "Spectator"
        success_message(f"  {my_role} socket initialized.")


def display_message_above_prompt(message, color=RESET):
    sys.stdout.write('\r\033[K')
    sys.stdout.flush()
    print(f"{color}{message}{RESET}")
    sys.stdout.write("  message_type: ")
    sys.stdout.flush()

def broadcast_presence_host():
    global BROADCAST_ACTIVE, broadcast_sock
    
    broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    broadcast_message_dict = {"message_type" : "ACTIVE", "host_addr" : (socket.gethostbyname(socket.gethostname()), PORT)}
    broadcast_message = json.dumps(broadcast_message_dict)

    while BROADCAST_ACTIVE:
        try:
            broadcast_sock.sendto(broadcast_message.encode(), ('255.255.255.255', BROADCAST_PORT))
        except OSError:
            break # Socket probably closed while thread is still looping
        time.sleep(3)


def host_received():
    global SESSION_ACTIVE

    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind(('', BROADCAST_PORT))
    listen_sock.settimeout(5)

    try:
        while True:
            data, addr = listen_sock.recvfrom(BUFFER_SIZE)
            message_dict = json.loads(data.decode())

            if message_dict.get("message_type") == "ACTIVE":
                success_message(f"  Joiner detected at {addr}")
                break

    except socket.timeout:
        SESSION_ACTIVE = False

    listen_sock.close()
    print(f"{BORDER}")


def listen_for_host():
    global SESSION_ACTIVE
    global peer_addr

    if my_role not in ["Peer", "Spectator"]:
        error_message("listen_for_host() should only be used by Joiner or Spectator.")
        return

    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind(('', BROADCAST_PORT))
    listen_sock.settimeout(5)

    retries = 0
    print("  Searching for host...")

    while retries < 3:
        try:
            data, addr = listen_sock.recvfrom(BUFFER_SIZE)
            message_dict = json.loads(data.decode())
            ip, port = addr

            if message_dict.get("message_type") == "ACTIVE":
                success_message(f"  Host Found ... Host IP: {ip}")

                # Save tuple("ip", portNumber)
                peer_addr = tuple(message_dict["host_addr"])
                info_message(f"  Connected to Host: {peer_addr}")
                break

        except socket.timeout:
            retries += 1
            if retries < 3:
                error_message(f"  No host detected... retrying ({retries}/3)")
                time.sleep(1)
            else:
                print("  No Host Found after 3 attempts, Program Terminating ...")
                SESSION_ACTIVE = False

    listen_sock.close()
    print(f"{BORDER}")


def validate_comm_mode(mode):

    valid_modes = ["P2P", "BROADCAST"]

    if mode is None:
        error_message("  Communication mode cannot be empty.")
        return False

    mode_clean = mode.strip().upper()

    if mode_clean not in valid_modes:
        error_message("  Invalid communication mode! Must be either P2P or Broadcast.")
        return False

    return mode_clean



def set_pokemon_data(pokemon_name, user):   

    global my_data, opponent_data

    name_clean = pokemon_name.strip().lower()

    pokemon_df["name_clean"] = pokemon_df["name"].astype(str).str.strip().str.lower()

    match = pokemon_df.loc[pokemon_df["name_clean"] == name_clean]

    if match.empty:
        error_message(f" Pokémon '{pokemon_name}' not found in dataset!")
        return None

    row = match.iloc[0].to_dict()   

    stats = {
        "hp": row['hp'],
        "attack": row['attack'],
        "defense": row['defense'],
        "special attack": row['sp_attack'],
        "special defense": row['sp_defense'],
        "speed": row['speed'],
        "type_1": row['type1'],
        "type_2": row['type2'],
        "row": row
    }

    if user == 1:
        my_data = stats
    else:
        opponent_data = stats
    
def receive_messages():
    while True:
        data, addr = my_socket.recvfrom(BUFFER_SIZE)
        message = data.decode()

        message_dict = json.loads(message)

        mes = message_dict["message_type"]

        if not mes in ["ACK", "DEFENSE_ANNOUNCE", "CALCULATION_REPORT", "CALCULATION_CONFIRM", "RESOLUTION_REQUEST"]:
            send_ack(message_dict, addr)
            if comm_mode == "BROADCAST" and my_role == "Host" and mes in ["ATTACK_ANNOUNCE", "DEFENSE_ANNOUNCE", "CALCULATION_REPORT", "CALCULATION_CONFIRM", "RESOLUTION_REQUEST", "RESOLUTION_CONFIRM", "CHAT_MESSAGE", "GAME_OVER"]:
                send_to_spectators(message, False)
    
        activity = check_activity(message_dict)
        process_activity(activity, message_dict, addr)

def send_ack(message, addr):
    send_message = json.dumps({
        "message_type" : "ACK",
        "ACK" : message["sequence_number"]
        })

    my_socket.sendto(send_message.encode(), addr)

def spectator_messages():
    global ack_received, my_name, seq
    
    while True:
        data, addr = my_socket.recvfrom(BUFFER_SIZE)
        message = data.decode()

        try:
            message_dict = json.loads(message)

            if message_dict["message_type"] == "SPECTATOR_ADMITTED":
                my_name = message_dict["name"]
                seq = message_dict["sequence_number"]
            elif (message_dict["message_type"] == "ACK") and (seq != 0):
                if message_dict["ACK"] == seq:
                    ack_received = True

            display_spectator_message(message_dict)
        except json.JSONDecodeError:
            print(f"{POKE_RED}[ERROR]{RESET} Invalid message format received.")
        except Exception as e:
            print(f"{POKE_RED}[ERROR]{RESET} processing message: {e}")

def display_spectator_message(message):
    if message["message_type"] == "ATTACK_ANNOUNCE":
        seq = message['sequence_number']
        display_message_above_prompt(BRED)
        title = "ATTACK ANNOUNCE"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_RED}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BRED)
        display_message_above_prompt(f"  message_type: ATTACK_ANNOUNCE",POKE_RED)
        display_message_above_prompt(f"  move_name: {message['move_name']}",POKE_RED)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_RED)
        display_message_above_prompt(BRED)

    elif message["message_type"] == "DEFENSE_ANNOUNCE":
        seq = message['sequence_number']
        display_message_above_prompt(BGREEN)
        title = "DEFENSE ANNOUNCE"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BGREEN)
        display_message_above_prompt(f"  message_type: DEFENSE_ANNOUNCE",POKE_GREEN)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_GREEN)
        display_message_above_prompt(BGREEN)
    
    elif message["message_type"] == "CALCULATION_REPORT":
        seq = message['sequence_number']
        display_message_above_prompt(BPURP)
        title = "CALCULATION REPORT"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_PURPLE}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BPURP)
        display_message_above_prompt(f"  message_type: CALCULATION_REPORT",POKE_PURPLE)
        display_message_above_prompt(f"  attacker: {message['attacker']}",POKE_PURPLE)
        display_message_above_prompt(f"  move_used: {message['move_used']}",POKE_PURPLE)
        display_message_above_prompt(f"  remaining_health: {message['remaining_health']}",POKE_PURPLE)
        display_message_above_prompt(f"  damage_dealt: {message['damage_dealt']}",POKE_PURPLE)
        display_message_above_prompt(f"  defender_hp_remaining: {message['defender_hp_remaining']}",POKE_PURPLE)
        display_message_above_prompt(f"  status_message: {message['status_message']}",POKE_PURPLE)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_PURPLE)
        display_message_above_prompt(BPURP)
    
    elif message["message_type"] == "CALCULATION_CONFIRM":
        seq = message['sequence_number']
        display_message_above_prompt(BGREEN)
        title = "CALCULATION CONFIRM"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BGREEN)
        display_message_above_prompt(f"  message_type: CALCULATION_CONFIRM",POKE_GREEN)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_GREEN)
        display_message_above_prompt(BGREEN)
    
    elif message["message_type"] == "RESOLUTION_REQUEST":
        seq = message['sequence_number']
        display_message_above_prompt(BYELLOW)
        title = "RESOLUTION REQUEST"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_YELLOW}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BYELLOW)
        display_message_above_prompt(f"  message_type: RESOLUTION_REQUEST",POKE_YELLOW)
        display_message_above_prompt(f"  attacker: {message['attacker']}",POKE_YELLOW)
        display_message_above_prompt(f"  move_used: {message['move_used']}",POKE_YELLOW)
        display_message_above_prompt(f"  damage_dealt: {message['damage_dealt']}",POKE_YELLOW)
        display_message_above_prompt(f"  defender_hp_remaining: {message['defender_hp_remaining']}",POKE_YELLOW)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_YELLOW)
        display_message_above_prompt(BYELLOW)
    
    elif message["message_type"] == "GAME_OVER":
        seq = message['sequence_number']
        display_message_above_prompt(BRED)
        title = "GAME OVER"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        print(f"{POKE_RED}{BOLD}{centered_title}{RESET}")
        print(BRED)
        print(f"  message_type: GAME_OVER",POKE_RED)
        print(f"  message_text: Program will terminate in 10 seconds",POKE_RED)
        print(f"  winner: {message['winner']}",POKE_GREEN)
        print(f"  loser: {message['loser']}",POKE_RED)
        print(f"  sequence_number: {message['sequence_number']}",POKE_RED)
        print(BRED)

        time.sleep(10)

        os.system('cls')

        print(BGREEN)
        title = "THANK YOU"
        inner_width = 70
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()
        print(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        print(BGREEN)
        print(f"{POKE_GREEN}  message_type: PROGRAM_TERMINATED{RESET}")
        print(f"{POKE_GREEN}  message_text: Thank you for SPECTATING!{RESET}")
        print(f"{POKE_GREEN}  winner: {message['winner']}{RESET}")
        print(f"{POKE_GREEN}  loser: {message['loser']}{RESET}")
        print(BGREEN)

        close_socket()
        os._exit(0)
    
    elif message["message_type"] == "CHAT_MESSAGE":
        seq = message['sequence_number']
        content_type = message.get('content_type', 'TEXT')
        sender = message.get('sender_name', 'Unknown')
        
        if content_type == "TEXT":
            display_message_above_prompt(BYELLOW)
            title = "CHAT MESSAGE"
            inner_width = 70  
            centered_title = title.center(inner_width)
            centered_title = " " + centered_title.rstrip()  
            display_message_above_prompt(f"{POKE_YELLOW}{BOLD}{centered_title}{RESET}")
            display_message_above_prompt(BYELLOW)
            display_message_above_prompt(f"\n  [CHAT] {sender}: {message.get('message_text', '')}",POKE_YELLOW)
        elif content_type == "STICKER":    
            display_message_above_prompt(BYELLOW)
            title = "CHAT MESSAGE"
            inner_width = 70  
            centered_title = title.center(inner_width)
            centered_title = " " + centered_title.rstrip()  
            display_message_above_prompt(f"{POKE_YELLOW}{BOLD}{centered_title}{RESET}")
            display_message_above_prompt(POKE_YELLOW)
            display_message_above_prompt(f"\n  [CHAT] {sender} sent a sticker (320x320px)",POKE_YELLOW)
            sticker_data = message.get('  sticker_data', '')
            if sticker_data:
                display_message_above_prompt(f"  Sticker size: {len(sticker_data)} bytes (Base64)",POKE_YELLOW)
        
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_YELLOW)
        display_message_above_prompt(BYELLOW)

    else:
        display_message_above_prompt(BPINK)
        title = "SPECTATOR MESSAGE"
        inner_width = 70
        centered_title = (" " + title.center(inner_width)).rstrip()
        display_message_above_prompt(f"{POKE_PINK}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BPINK)
        display_message_above_prompt(f"  [SPECTATOR] Received {message} message", POKE_PINK)
        display_message_above_prompt(f"Content: {message}", POKE_PINK)
        display_message_above_prompt(BPINK)

    
def send_to_spectators(message, from_host):
    if from_host:
        mes = json.loads(message)
        mes["sender"] = "Player 1"
        mes = json.dumps(mes)
    else:
        mes = json.loads(message)
        mes["sender"] = "Player 2"
        mes = json.dumps(mes)

    for addr in spectators:
        my_socket.sendto(mes.encode(), addr)

def check_activity(message): 
    if message["message_type"] == "HANDSHAKE_REQUEST":
        return 1
    elif message["message_type"] == "HANDSHAKE_RESPONSE":
        return 2
    elif message["message_type"] == "SPECTATOR_REQUEST":
        return 3
    elif message["message_type"] == "BATTLE_SETUP":
        return 4
    elif message["message_type"] == "ATTACK_ANNOUNCE":
        return 5
    elif message["message_type"] == "DEFENSE_ANNOUNCE":
        return 6
    elif message["message_type"] == "CALCULATION_REPORT":
        return 7
    elif message["message_type"] == "CALCULATION_CONFIRM":
        return 8
    elif message["message_type"] == "RESOLUTION_REQUEST":
        return 9
    elif message["message_type"] == "GAME_OVER":
        return 10
    elif message["message_type"] == "CHAT_MESSAGE":
        return 11
    elif message["message_type"] == "ACK":
        return 12
    else:
        return 0
    
def validate_move(move_name):
    global sp_count
    # Check if move exists in pokemon_moves
    move = next((m for m in pokemon_moves if m["name"].lower() == move_name.lower()), None)
    if not move:
        return False

    type1 = my_data["type_1"]
    type2 = my_data["type_2"]

    if type2 is None or isinstance(type2, float):
        type2 = "none"

    if move["category"] == "Special" and sp_count == MAX_SP_USES:
        return False

    # Check if move type matches either of the Pokémon's types
    if move["type"].lower() == type1.lower() or move["type"].lower() == type2.lower():
        if move["category"] == "Special":
            sp_count += 1
        return True
    else:
        return False

def calculation_report():
    if last_move_name:
        damage_result = calculate_damage(is_attacker=True)
        attacker = my_pokemon
        move_used = last_move_name
    elif last_opponent_move:
        damage_result = calculate_damage(is_attacker=False)
        attacker = opponent_pokemon
        move_used = last_opponent_move
    else:
        error_message("Error: No attack move recorded. Cannot generate calculation report.")
        return

    send_message = {
        "message_type" : "CALCULATION_REPORT",
        "attacker" : attacker,
        "move_used" : move_used,
        "remaining_health" : int(damage_result["attacker_hp_after"]),
        "damage_dealt" : int(damage_result["damage"]),
        "defender_hp_remaining" : int(damage_result["defender_hp_after"]),
        "status_message" : f"{attacker} used {move_used}! It was super effective!",
        "sequence_number" : seq
    }

    my_socket.sendto(json.dumps(send_message).encode(), peer_addr) 

def calculation_confirm():
    global attacker, last_move_name, last_opponent_move, SESSION_ACTIVE, BROADCAST_ACTIVE, next_attacker

    display_message_above_prompt("message_type: CALCULATION_CONFIRM")
    display_message_above_prompt(f"sequence_number: {seq}")

    send_message = {"message_type" : "CALCULATION_CONFIRM", "sequence_number" : seq}
    my_socket.sendto(json.dumps(send_message).encode(), peer_addr)

    if opponent_data["hp"] <= 0 or my_data["hp"] <= 0:
        if opponent_data["hp"] <= 0:
            winner = my_pokemon
            loser = opponent_pokemon
        else:
            winner = opponent_pokemon
            loser = my_pokemon
    
        message_type = "GAME_OVER"
        display_message_above_prompt("message_type: ", message_type)
        display_message_above_prompt("sequence_number: ", seq)
        send_message = {
            "message_type": message_type,
            "winner": winner,
            "loser": loser,
            "sequence_number" : seq
        }

        my_socket.sendto(json.dumps(send_message).encode(), peer_addr)
 
    else:
        if last_move_name:
            next_attacker = opponent_pokemon
        else:
            next_attacker = my_pokemon

        attacker = None
        last_move_name = None
        last_opponent_move = None

def resolution_request():
    global SESSION_ACTIVE, BROADCAST_ACTIVE
    display_message_above_prompt(f"sequence_number: {seq}")

    if last_move_name:
        move_used = last_move_name
    else:
        move_used = last_opponent_move

    send_message = {
        "message_type" : "RESOLUTION_REQUEST",
        "attacker" : damage_result["attacker"],
        "move_used" : damage_result["move"],
        "damage_dealt" : int(damage_result["damage"]),
        "defender_hp_remaining" : int(damage_result["defender_hp_after"]),
        "sequence_number" : seq
    }

    count = 0

    if resolution == False and count == 0:
        my_socket.sendto(json.dumps(send_message).encode(), peer_addr) 
        count += 1
        time.sleep(0.5)

    if resolution == False and count == 1:
        SESSION_ACTIVE = False
        BROADCAST_ACTIVE = False
        display_message_above_prompt(BRED)
        title = "DISCREPANCY ERROR"
        inner_width = 70
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()
        display_message_above_prompt(f"{POKE_RED}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BRED)
        display_message_above_prompt(f"  message_type: GAME_TERMINATED", BRED)
        display_message_above_prompt(f"  message_text: DISCREPANCY ERROR ON BOTH SIDES", BRED)
        display_message_above_prompt(f"  sequence_number: {seq}", BRED)
        display_message_above_prompt(BRED)

        time.sleep(3)

        os.system('cls')
        print(BGREEN)
        title = "THANK YOU"
        inner_width = 70
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()
        print(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        print(BGREEN)
        print(f"{POKE_GREEN}  message_type: PROGRAM_TERMINATED{RESET}")
        print(f"{POKE_GREEN}  message_text: Thank you for PLAYING!{RESET}")
        print(BGREEN)

        os._exit(0)

def process_activity(activity, message, addr):
    global seed, peer_addr, battle_state, my_pokemon, opponent_pokemon, comm_mode, seq, my_name, ack_received, SESSION_ACTIVE, BROADCAST_ACTIVE, next_attacker, resolution

    if activity == 1:
        seq = message["sequence_number"]
        peer_addr = addr

        display_message_above_prompt(BGOLD)
        title = "HANDSHAKE REQUEST"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_GOLD}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BGOLD)
        display_message_above_prompt(f"  message_type: HANDSHAKE_REQUEST")
        display_message_above_prompt(f"  message_text: Peer is requesting for handshake")
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}\n  RESPOND HANDSHAKE_RESPONSE")
        display_message_above_prompt(BGOLD)

    elif activity == 2: 
        my_name = "Player2"
        seq = message["sequence_number"]

        display_message_above_prompt(BGOLD)
        title = "HANDSHAKE RESPONSE"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_GOLD}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BGOLD)
        display_message_above_prompt(f"  message_type: HANDSHAKE_RESPONSE")
        display_message_above_prompt(f"  message_text: The host responded to your handshake request")
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}\n  Expect Battle-Setup from Host")
        display_message_above_prompt(BGOLD)

    elif activity == 3:
        global spectator_count, spectators

        spectator_count += 1
        spectators.append(addr)
        seq += 1
        message_dict = {"message_type" : "SPECTATOR_ADMITTED","name" : "Spectator" + str(spectator_count), "sequence_number" : seq} # Not sure if needed to seed spectator
        message = json.dumps(message_dict)
        my_socket.sendto(message.encode(), addr)

        display_message_above_prompt(BPINK)
        title = "SPECTATOR REQUEST"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_PINK}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BPINK)
        display_message_above_prompt(f"  message_type: SPECTATOR_REQUEST")
        display_message_above_prompt(f"  spectator_name: {message_dict["name"]}")
        display_message_above_prompt(f"  sequence_number: {seq}\n  Use BROADCAST mode to spectate battle")
        display_message_above_prompt(BPINK)
        ack_received = False

    elif activity == 4: 
        opponent_pokemon = message["pokemon_name"]
        set_pokemon_data(opponent_pokemon, 2)
        comm_mode = message["communication_mode"]
        seq = message["sequence_number"]

        if my_role == "Peer":
            next_attacker = opponent_pokemon

        display_message_above_prompt(BBLUE)
        title = "BATTLE SETUP"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_BLUE}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BBLUE)
        display_message_above_prompt(f"  message_type: BATTLE_SETUP", POKE_BLUE)
        display_message_above_prompt(f"  communication_mode: {comm_mode}", POKE_BLUE)
        display_message_above_prompt(f"  pokemon_name: {opponent_pokemon}", POKE_BLUE)
        display_message_above_prompt(f"  stat_boosts: {message['stat_boosts']}", POKE_BLUE)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}", POKE_BLUE)
        display_message_above_prompt(BBLUE)

    elif activity == 5: 
        global last_opponent_move, attacker
        resolution = False
        seq = message['sequence_number']
        last_opponent_move = message['move_name']  
        attacker = opponent_pokemon

        display_message_above_prompt(BRED)
        title = "ATTACK ANNOUNCE"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_RED}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BRED)
        display_message_above_prompt(f"  message_type: ATTACK_ANNOUNCE", POKE_RED)
        display_message_above_prompt(f"  move_name: {message['move_name']}", POKE_RED)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}", POKE_RED)
        display_message_above_prompt(BRED)

        seq += 1
        display_message_above_prompt("message_type: DEFENSE_ANNOUNCE")
        display_message_above_prompt("sequence_number: ", seq)
        send_message = {
            "message_type" : "DEFENSE_ANNOUNCE",
            "sequence_number" : seq
        }

        my_socket.sendto(json.dumps(send_message).encode(), peer_addr)
        calculation_report()

    elif activity == 6: 
        seq = message['sequence_number']

        display_message_above_prompt(BGREEN)
        title = "DEFENSE ANNOUNCE"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BGREEN)
        display_message_above_prompt(f"  message_type: DEFENSE_ANNOUNCE", POKE_GREEN)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}", POKE_GREEN)
        display_message_above_prompt(BGREEN)


    elif activity == 7: 
        seq = message['sequence_number']

        display_message_above_prompt(BPURP)
        title = "CALCULATION REPORT"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_PURPLE}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BPURP)
        display_message_above_prompt(f"  message_type: CALCULATION_REPORT",POKE_PURPLE)
        display_message_above_prompt(f"  attacker: {message['attacker']}",POKE_PURPLE)
        display_message_above_prompt(f"  move_used: {message['move_used']}",POKE_PURPLE)
        display_message_above_prompt(f"  remaining_health: {message['remaining_health']}",POKE_PURPLE)
        display_message_above_prompt(f"  damage_dealt: {message['damage_dealt']}",POKE_PURPLE)
        display_message_above_prompt(f"  defender_hp_remaining: {message['defender_hp_remaining']}",POKE_PURPLE)
        display_message_above_prompt(f"  status_message: {message['status_message']}",POKE_PURPLE)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_PURPLE)
        display_message_above_prompt(BPURP)

        if attacker == my_pokemon:
            calculation_report()

        if attacker == my_pokemon:
            rem_health = int(my_data["hp"])
            def_health = int(opponent_data["hp"])
        else:
            rem_health = int(opponent_data["hp"])
            def_health = int(my_data["hp"])

        if message["remaining_health"] == rem_health and message["defender_hp_remaining"] == def_health:
            calculation_confirm()
        else:
            resolution_request()

    elif activity == 8: 
        seq = message['sequence_number']

        display_message_above_prompt(BGREEN)
        title = "CALCULATION CONFIRM"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BGREEN)
        display_message_above_prompt(f"  message_type: CALCULATION_CONFIRM",POKE_GREEN)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_GREEN)
        display_message_above_prompt(BGREEN)

        resolution = True

    elif activity == 9: 
        seq = message['sequence_number']

        display_message_above_prompt(BYELLOW)
        title = "RESOLUTION REQUEST"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_YELLOW}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BYELLOW)
        display_message_above_prompt(f"  message_type: RESOLUTION_REQUEST",POKE_YELLOW)
        display_message_above_prompt(f"  attacker: {message['attacker']}",POKE_YELLOW)
        display_message_above_prompt(f"  move_used: {message['move_used']}",POKE_YELLOW)
        display_message_above_prompt(f"  damage_dealt: {message['damage_dealt']}",POKE_YELLOW)
        display_message_above_prompt(f"  defender_hp_remaining: {message['defender_hp_remaining']}",POKE_YELLOW)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}",POKE_YELLOW)
        display_message_above_prompt(BYELLOW)

        seq += 1
        if int(message["defender_hp_remaining"]) == int(opponent_data["hp"]):
            send_message = {"message_type" : "CALCULATION_CONFIRM", "sequence_number" : seq}
            my_socket.sendto(json.dumps(send_message).encode(), peer_addr)

    elif activity == 10: 
        seq = message['sequence_number']
        print(BRED)
        title = "GAME OVER"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        print(f"{POKE_RED}{BOLD}{centered_title}{RESET}")
        print(BRED)
        print(f"  message_type: GAME_OVER",POKE_RED)
        print(f"  message_text: Program will terminate in 10 seconds",POKE_RED)
        print(f"  winner: {message['winner']}",POKE_GREEN)
        print(f"  loser: {message['loser']}",POKE_RED)
        print(f"  sequence_number: {message['sequence_number']}",POKE_RED)
        print(BRED)

        time.sleep(10)

        os.system('cls')

        print(BGREEN)
        title = "THANK YOU"
        inner_width = 70
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()
        print(f"{POKE_GREEN}{BOLD}{centered_title}{RESET}")
        print(BGREEN)
        print(f"{POKE_GREEN}  message_type: PROGRAM_TERMINATED{RESET}")
        print(f"{POKE_GREEN}  message_text: Thank you for PLAYING!{RESET}")
        print(f"{POKE_GREEN}  winner: {message['winner']}{RESET}")
        print(f"{POKE_GREEN}  loser: {message['loser']}{RESET}")
        print(BGREEN)

        os._exit(0)

        SESSION_ACTIVE = False
        BROADCAST_ACTIVE = False

    elif activity == 11: 
        seq = message['sequence_number']

        if (addr != peer_addr) and (comm_mode == "BROADCAST") and (my_role == "Host"): # Spectator's message should be broadcasted to spectators if comm_mode is BROADCAST
            my_socket.sendto(json.dumps(message).encode(), peer_addr)

        display_message_above_prompt(BYELLOW)
        title = "CHAT MESSAGE"
        inner_width = 70  
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()  
        display_message_above_prompt(f"{POKE_YELLOW}{BOLD}{centered_title}{RESET}")
        display_message_above_prompt(BYELLOW)
        display_message_above_prompt(f"  message_type: CHAT_MESSAGE", POKE_YELLOW)
        display_message_above_prompt(f"  sender_name: {message["sender_name"]}", POKE_YELLOW)
        display_message_above_prompt(f"  content_type: {message["content_type"]}", POKE_YELLOW)
        display_message_above_prompt(f"  message_text: {message["message_text"]}", POKE_YELLOW)
        display_message_above_prompt(f"  sequence_number: {message['sequence_number']}", POKE_YELLOW)
        display_message_above_prompt(BYELLOW)

    elif activity == 12: 
        if seq == message["ACK"]:
            ack_received = True

def get_move(move_name):
    for move in pokemon_moves:
        if move["name"].lower() == move_name.lower():
            return move
    return None 

def get_type_multipliers(move_type, defender_data):
    row = defender_data["row"]
    col_name = f"against_{move_type.lower()}" # Extract the defender's against x
    combined = row.get(col_name, 1.0) # 1.0 is default if col_name doesn't exist

    type1_effectiveness = combined # already includes both type
    type2_effectiveness = 1.0

    return type1_effectiveness, type2_effectiveness

def calculate_damage(is_attacker = True):
    global my_data, opponent_data, last_move_name, last_opponent_move, move_name_to_use, damage_result #move_name_to_use is the user input move

    if is_attacker:
        move_name_to_use = last_move_name
        attacker = my_pokemon
        attacker_data = my_data
        defender_data = opponent_data
    else:
        move_name_to_use = last_opponent_move
        attacker = opponent_pokemon
        attacker_data = opponent_data
        defender_data = my_data

    move = get_move(move_name_to_use)

    if move is None:
        return {
            "damage": 0,
            "defender_hp_before": defender_data["hp"],
            "defender_hp_after": defender_data["hp"],
            "attacker_hp_after": attacker_data["hp"],
            "type1_effectiveness": 1.0,
            "type2_effectiveness": 1.0,
            "move_type": None,
            "damage_category": None,
            "base_power": 0
        }

    # Extract necessary fields for calculation
    move_type = move["type"]
    damage_category = move["category"]
    base_power = move["power"]

    if damage_category.lower() == "physical":
        attacker_stat = attacker_data["attack"] 
        defender_stat = defender_data["defense"] 
    else: 
        attacker_stat = attacker_data["special attack"]
        defender_stat = defender_data["special defense"]

    type1_eff, type2_eff = get_type_multipliers(move_type, defender_data)

    if defender_stat <= 0:
        defender_stat = 1

    damage = (base_power * attacker_stat * type1_eff * type2_eff) / defender_stat
    defender_hp_before = defender_data["hp"]
    defender_hp_after = defender_hp_before - damage
    defender_data["hp"] = defender_hp_after 
    attacker_hp_after = attacker_data["hp"]

    dict_stats = {
        "damage": damage,
        "defender_hp_before": defender_hp_before,
        "defender_hp_after": defender_hp_after,
        "attacker_hp_after": attacker_hp_after,
        "type1_effectiveness": type1_eff,
        "type2_effectiveness": type2_eff,
        "move_type": move_type,
        "damage_category": damage_category,
        "base_power": base_power,
        "attacker" : attacker,
        "move" : move_name_to_use
    }

    damage_result = dict_stats
    return dict_stats

def build_calculation_confirm(seq): 
    return {
        "message_type": "CALCULATION_CONFIRM",
        "sequence_number": seq
    }

def send_calculation_confirm(sock, seq): 
    msg = build_calculation_confirm(seq)
    encoded = json.dumps(msg).encode()
    sock.sendall(encoded)
    print(f"[SENT] CALCULATION_CONFIRM (seq={seq})")

def build_resolution_request(attacker, move_used, damage_dealt, defender_hp_remaining, seq): 
    return {
        "message_type": "RESOLUTION_REQUEST",
        "attacker": attacker,
        "move_used": move_used,
        "damage_dealt": damage_dealt,
        "defender_hp_remaining": defender_hp_remaining,
        "sequence_number": seq
    }

def send_resolution_request(sock, attacker, move_used, damage_dealt, defender_hp_remaining, seq):
    msg = build_resolution_request(attacker, move_used, damage_dealt, defender_hp_remaining, seq)
    encoded = json.dumps(msg).encode()
    sock.sendall(encoded)
    print(f"[SENT] RESOLUTION_REQUEST (seq={seq})")

def get_pokemon(name, data):
    if not name:
        return None
    return data.get(name.strip().lower())

def close_socket():
    global BROADCAST_ACTIVE, broadcast_sock

    BROADCAST_ACTIVE = False
    try:
        my_socket.close()
    except Exception:
        pass

    # close broadcast socket if we are Host and it exists
    if my_role == "Host" and broadcast_sock is not None:
        try:
            broadcast_sock.close()
        except Exception:
            pass
        broadcast_sock = None
        
# Main Program
try:
    pokemon_df = pd.read_csv("pokemon.csv")
except FileNotFoundError:
    print("Error: pokemon.csv not found!")
    sys.exit(1)

pokemon_data = {
    str(row["name"]).lower(): row
    for _, row in pokemon_df.iterrows()
}

welcome_message()
create_socket()

if my_role == "Host":
    host_received()
    if SESSION_ACTIVE:
        SESSION_ACTIVE = False
        print("Another host is running, Program Closing ...")
    else:
        broadcast_thread = threading.Thread(target=broadcast_presence_host, daemon=True)
        broadcast_thread.start()
        SESSION_ACTIVE = True
elif my_role in ["Peer", "Spectator"]:
    listen_for_host()

if SESSION_ACTIVE:
    if my_role != "Spectator":
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
    elif my_role == "Spectator":
        spectator_thread = threading.Thread(target=spectator_messages, daemon=True)
        spectator_thread.start()

while SESSION_ACTIVE:
    ack_received = False
    message_sent_count = 0
    message_type = input(prompt_label("message_type: "))

    if message_type == "ATTACK_ANNOUNCE" and next_attacker != my_pokemon:
        display_message_above_prompt("  Cannot Attack Yet. Wait for your opponent's turn.")
        continue

    if message_type == "BATTLE_SETUP":
        while True:
            comm_input = input(prompt_label("communication_mode [P2P/Broadcast]: "))
            comm_validated = validate_comm_mode(comm_input)
            if comm_validated:
                break
            
        comm_input = comm_validated  # normalized (P2P or BROADCAST)


        while True:
            my_pokemon = input(prompt_label("pokemon_name: "))

            if get_pokemon(my_pokemon, pokemon_data) is not None:
                break
            else:
                print(f"Error: Pokémon '{my_pokemon}' does not exist. Try again.\n")
        
        set_pokemon_data(my_pokemon, 1)
        print(f"{POKE_YELLOW}stat_boosts : {{\"special_attack_uses\" : 5, \"special_defense_uses\" : 5}}{RESET}")

        if my_role == "Host":
            comm_mode = comm_input
            next_attacker = my_pokemon

        send_message = {
            "message_type" : message_type, 
            "communication_mode" : comm_input, 
            "pokemon_name" : my_pokemon, 
            "stat_boosts" : "{\"special_attack_uses\" : 5, \"special_defense_uses\" : 5}"
        }

    elif message_type == "ATTACK_ANNOUNCE":
        move_input = input(prompt_label("move_name: "))
        attacker = my_pokemon

        while not validate_move(move_input):
            display_message_above_prompt("  Invalid move! Please input move corresponding to Type!")
            move_input = input(prompt_label("move_name: "))

        last_move_name = move_input

        display_message_above_prompt("sequence_number: ", seq)
        send_message = {
            "message_type" : message_type, 
            "move_name" : move_input,
            "sequence_number" : seq
        }

    elif message_type == "RESOLUTION_REQUEST":
        resolution = False
        resolution_request()

    elif message_type == "CHAT_MESSAGE":
        print(f"{POKE_YELLOW}sender_name: {my_name}{RESET}")  

        # ask for TEXT o STICKER and force uppercase + validate
        while True:
            content_input = input(prompt_label("content_type (TEXT/STICKER): ")).strip().upper()
            if content_input in ("TEXT", "STICKER"):
                break
            display_message_above_prompt("  Invalid content type! Please enter TEXT or STICKER.")

        if content_input == "TEXT":
            msg_input = input(prompt_label("message_text: "))
            send_message = {
                "message_type" : message_type, 
                "sender_name" : my_name, 
                "content_type" : "TEXT", 
                "message_text" : msg_input
            }
        else:
            sticker_data = None

            while sticker_data is None:
                sticker_file = input(prompt_label("sticker_file_path: ")).strip().strip('"')

                if not os.path.isfile(sticker_file):
                    display_message_above_prompt("  File not found. Please enter a valid path.")
                    continue

                # < 10 MB as per RFC
                file_size = os.path.getsize(sticker_file)
                if file_size > 10 * 1024 * 1024:
                    display_message_above_prompt("  Sticker must be <= 10MB. Please choose a smaller file.")
                    continue

                # Optional: check dimensions 320x320 if Pillow is installed
                try:
                    with Image.open(sticker_file) as img:
                        width, height = img.size
                    if width != 320 or height != 320:
                        display_message_above_prompt("  Sticker must be exactly 320x320px. Please choose another image.")
                        continue
                except ImportError:
                    display_message_above_prompt("  (Warning: Pillow not installed, skipping dimension check)")

                try:
                    with open(sticker_file, "rb") as f:
                        sticker_data = base64.b64encode(f.read()).decode()
                except Exception as e:
                    display_message_above_prompt(f"  Error reading sticker file: {e}")
                    sticker_data = None

            send_message = {
                "message_type": message_type,
                "sender_name": my_name,
                "content_type": "STICKER",
                "sticker_data": sticker_data
            }

    else: 
        send_message = {"message_type" : message_type}

    while (not ack_received) and (message_sent_count < MAX_RETRIES) and (not message_type == "RESOLUTION_REQUEST"): # To prevent mismatch in SEQ. I inserted the incrementation before sending the message to accurately retrieve the latest SEQ.
        if message_sent_count == 0:
            seq += 1
            send_message["sequence_number"] = seq

            if comm_mode == "BROADCAST" and my_role == "Host":
                send_to_spectators(json.dumps(send_message), True)

        if (my_role == "Spectator") and (seq == 0):
            ack_received = True

        my_socket.sendto(json.dumps(send_message).encode(), peer_addr)
        message_sent_count += 1
        time.sleep(0.5)

    if(message_sent_count == MAX_RETRIES):
        print(BRED)
        title = "DISCONNECTED"
        inner_width = 70
        centered_title = title.center(inner_width)
        centered_title = " " + centered_title.rstrip()
        print(f"{POKE_RED}{BOLD}{centered_title}{RESET}")
        print(BRED)
        display_message_above_prompt(f"  message_type: CONNECTION_LOST",POKE_RED)
        display_message_above_prompt(f"  message_text: Maximum retries with no ack from peer\n  Terminating Program!",POKE_RED)
        print(BRED)
        SESSION_ACTIVE = False