# P2P Pokemon Battle Application (PokeProtocol over UDP)

This project is a console-based peer-to-peer Pokemon battle application built in Python.  
It implements the core ideas of the [PokeProtocol RFC](RFC%20PokeProtocol.pdf) over **UDP**.

The application uses the [pokemon.csv](pokemon.csv) dataset provided by our professor to look up Pokemon stats and type effectiveness.

---

## Requirements

- **Python**: 3.8+ (recommended)
- **Dependencies** (install via `pip`):

  ```bash
  pip install -r requirements.txt
  ```

---

## Task Matrix / Group Continbutions
**Group Members:** Chiu, Helaga, Mojica, Ramirez
| Task Area         | Description                                                         | Member Assigned |
|-------------------|---------------------------------------------------------------------|-----------------|
| Protocol Design   | Mapped RFC to message types and states                              |                 |
| Networking (UDP)  | Socket setup, host/peer flow, ports, broadcast                      |                 |
| Reliability Layer | Sequence numbers, ACKs, retries, timeout logic                      |                 |
| Data Handling     | Loading [pokemon.csv](pokemon.csv), name matching, type multipliers |                 |
| Battle Logic      | Move list, damage formula, turn flow, HP updates                    |                 |
| Chat (Text)       | CHAT_MESSAGE structure, player chat display                         |                 |
| Chat (Stickers)   | File validation, base64 encoding, sticker display                   |                 |
| Spectator Mode    | Handling of SPECTATOR_REQUEST, broadcasting to spectators           |                 |
| Documentation     | Writing README, instructions, task matrix                           |                 |
| Review            | Refactoring                                                         |                 |

---

## Features

- **Three Roles**
  - **Host** – creates a battle lobby, broadcasts presence, and fights against a peer.
  - **Peer** – joins a host and engages in a 1-v-1 Pokemon battle.
  - **Spectator** – connects to a host in broadcast mode and watches the battle (and chat).

- **Pokemon & Moves**
  - Loads Pokemon stats from `pokemon.csv` via `pandas`.
  - Player chooses a Pokemon by name (normalized to match the dataset).
  - Fixed move list with:
    - `name`
    - `category` (Physical / Special)
    - `type`
    - `power`
  - Move validation enforces that chosen moves are compatible with the Pokemon’s type.

- **Damage Calculation**
  - TODO

- **Networking**
  - TODO
- **Chat & Stickers**
  - `CHAT_MESSAGE` supports:
    - `TEXT` (plain chat message)
    - `STICKER` (image sent as Base64)
  - Stickers are loaded from an image file, checked, and encoded using `Pillow` (`PIL.Image`) before sending.