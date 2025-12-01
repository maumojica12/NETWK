# P2P Pokemon Battle Application (PokeProtocol over UDP)
A CSNETWK Machine Project

This project is a console-based peer-to-peer Pokemon battle application built in Python.  
It implements the core ideas of the [PokeProtocol RFC](RFC%20PokeProtocol.pdf) over **UDP**.

The application uses the [pokemon.csv](pokemon.csv) dataset provided by our professor to look up Pokemon stats and type effectiveness.

---

# Table of Contents

  A. Overview  
  B. Requirements  
  C. Task Matrix / Group Contributions  
  D. Roles  
  E. Communication Model  
  F. Message Types  
  G. Battle Mechanics  
  H. Damage Calculation   
  I. Chat & Sticker System    
  J. Discrepancy Handling   
  K. Running the Program  
  L. Error Handling & Edge Cases  
  M. Files and Dependencies  
  N. Declaration of AI Usage  

# A. Overview

  I. Description
    PokeProtocol is a UDP-powered turn-based Pokémon battle simulator with:  
      
      a. Real-time messaging  
      b. Independent calculation validation  
      c. Spectator broadcasts  
      d. ANSI-styled terminal UI  
      e. Chat system with text and stickers  
      f. It supports Host, Peer, and Spectator roles and ensures reliable turn-based gameplay with sequence numbers, ACKs, and retries  
  
  II. Features  

      a. Turn-based combat with move validation
      b. Damage calculation based on stats, move power, and type effectiveness
      c. Spectator mode with live updates
      d. Chat and sticker support
      e. Sequence-number-based reliability
      f. Discrepancy detection with resolution requests
      g. Styled ANSI terminal interface

# B. Requirements

  - **Python**: 3.8+ (recommended)
  - **Dependencies** (install via `pip`):

    ```bash
    pip install -r requirements.txt
    ```

# C. Task Matrix / Group Contributions  

**Group Members:** Chiu, Helaga, Mojica, Ramirez
| Task Area         | Description                                                         | Member Assigned |
|-------------------|---------------------------------------------------------------------|-----------------|
| Protocol Design   | Mapped RFC to message types and states                              |  Chiu           |
| Networking (UDP)  | Socket setup, host/peer flow, ports, broadcast                      |  Mojica         |
| Reliability Layer | Sequence numbers, ACKs, retries, timeout logic                      |  Helaga         |
| Data Handling     | Loading [pokemon.csv](pokemon.csv), name matching, type multipliers |  Mojica         |
| Battle Logic      | Move list, damage formula, turn flow, HP updates                    |  Chiu, Ramirez  |
| Chat (Text)       | CHAT_MESSAGE structure, player chat display                         |  Ramirez        |
| Chat (Stickers)   | File validation, base64 encoding, sticker display                   |  Helaga         |
| Spectator Mode    | Handling of SPECTATOR_REQUEST, broadcasting to spectators           |  Ramirez        |
| Documentation     | Writing README, instructions, task matrix                           |  Chiu, Mojica   |
| Review            | Refactoring                                                         |  Helaga         |

# D. Roles

  I. Host

    a. Creates and manages the lobby  
    b. Accepts Peer connections
    c. Can broadcast events to Spectators
    d. Chooses communication mode (P2P/Broadcast)
    e. Initiates Pokémon selection and battle setup

  II. Peer

    a. Joins a Host lobby
    b. Engages in 1v1 battles
    c. Can send chat messages (TEXT or STICKER)

  III. Spectator

    a. Connects to Host via broadcast
    b. Receives all battle updates and chat
    c. Cannot send battle moves
    d. Can send chat messages (TEXT or STICKER)

# E. Communication Model

  Two main UDP channels:

    a. Direct battle communication -> 5432
    b. Host broadcast for discovery	-> 5217

  The protocol relies on sequence numbers and ACKs to ensure message ordering and reliability.

# F. Message Types
  Message Type         | Direction          | Description                                        |
|----------------------|--------------------|----------------------------------------------------|
| HANDSHAKE_REQUEST    | Peer → Host        | Peer	Request to join match                        |
| HANDSHAKE_RESPONSE	 |  Host → Peer	      | Accepts handshake                                  |
  BATTLE_SETUP	       | Both	              | Pokémon selection, stat boosts, communication mode |
  ATTACK_ANNOUNCE	     | Player → Opponent	| Announces move                                     |
  DEFENSE_ANNOUNCE	   | Opponent → Player	| Prepares for damage calculation                    |
  CALCULATION_REPORT	 | Both	              | Shares damage, HP, move stats                      |
  CALCULATION_CONFIRM	 | Both	              | Confirms calculation match                         |
  RESOLUTION_REQUEST	 | Any	              | Triggered if mismatch occurs                       |
  GAME_OVER	           | Host → All	        | Sent when Pokémon reaches 0 HP                     |
  CHAT_MESSAGE	       | Any	              | TEXT or STICKER messages                           |

# G. Battle Mechanics

  1. Players can select Pokémon using names in pokemon.csv.
  2. Each Pokémon has stats: hp, attack, defense, special attack, special defense, speed, type1, type2.
  3. Stat boosts for special moves (special_attack_uses, special_defense_uses) are tracked.
  4. Move validation ensures type compatibility.
  5. Turn order is enforced; players cannot attack out of turn.
  6. Each attack is broadcast to opponent (and spectators in broadcast mode).
  7. Sequence numbers ensure proper turn ordering.

# H. Damage Calculation  

  ```bash
    damage = (power × attacker_stat × type1_multiplier × type2_multiplier) / defender_stat
  ```

  a. Calculated independently by both players.  
  b. Updates defender HP immediately.  
  c. Includes Physical vs Special move differentiation.  
  d. Type effectiveness multipliers from pokemon.csv   

# I. Chat & Sticker System

  a. TEXT: Plain text messages  
  b. STICKER:  
    - PNG files converted to Base64  
    - Max file size: 10MB  
    - Recommended dimensions: 320x320px  
    - Stickers are validated and optionally displayed in ASCII in the console  
  
# J. Discrepancy Handling  

  If calculation results differ:  
    - RESOLUTION_REQUEST is sent  
    - Players verify computations  
    - Ensures fairness and synchronization  

# K. Running the Program 

  ```bash
    HOST
    python FINAL.py
    Role: Host
  ```
  ```bash
    PEER
    python FINAL.py
    Role: Peer
  ```
  ```bash
    SPECTATOR
    python FINAL.py
    Role: Spectator
  ```

# L. Error Handling & Edge Cases

1. Invalid Pokémon name → reprompt  
2. Invalid move → reprompt  
3. File not found for sticker → reprompt  
4. Sticker exceeds 10MB → reprompt  
5. Pokémon calculation mismatch → RESOLUTION_REQUEST  
6. 3 failed retries for ACK → terminate connection  

# M. Files and Dependencies 

  1. CSNETWK_MP.py	Main program
  2. pokemon.csv	Pokémon stats and types
  3. sticker.png
  4. requirements.txt

# N. Declaration of AI Usage  

Parts of this project’s documentation and formatting were assisted using OpenAI ChatGPT for:

  1. Organizing protocol descriptions
  2. Clarifying feature lists (e.g., spectator mode, validation steps)
  3. Formatting the README into a Markdown-ready layout
  4. Improving clarity and consistency
  5. Categorizing features for readability
 