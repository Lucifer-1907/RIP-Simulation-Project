# RIP Protocol Simulation

A visual simulation of the Routing Information Protocol (RIP) distance-vector algorithm,
with animated router and packet images.

---

## Requirements

- **Python 3.8 or higher**
- **Pillow** (for image assets) — install with:
  ```
  pip install pillow
  ```
  > If Pillow is not installed, the simulation still runs using plain coloured shapes as fallback.

---

## How to Run

### Windows
1. Install Python from https://python.org (check "Add Python to PATH")
2. Open Command Prompt in the project folder and run:
   ```
   pip install pillow
   python main.py
   ```

### macOS
```bash
pip3 install pillow
python3 main.py
```

### Linux
```bash
# Install tkinter if missing (only needed once)
sudo apt install python3-tk      # Debian / Ubuntu
sudo pacman -S tk                # Arch / CachyOS / Manjaro

pip install pillow
python3 main.py
```

---

## Project Structure

```
rip-sim/
├── main.py                # Entry point
├── gui.py                 # Tkinter GUI (topology editor + simulation)
├── router.py              # Router class and distance-vector logic
├── rip_algorithm.py       # One round of RIP update
├── network_topology.py    # Load topology from file
├── utils.py               # Shared constants and formatting helpers
├── test_rip.py            # Headless test (no GUI needed)
├── assets/
│   ├── router.png         # Router node image
│   └── packet.png         # Travelling packet/message image
└── data/
    └── topology.txt       # Default topology loaded on startup
```

---

## Running Without GUI (Headless Test)

```bash
python3 test_rip.py
```

---

## Topology File Format (data/topology.txt)

Each line defines one undirected link:
```
R1 R2
R2 R3
R3 R4
```

You can also define the topology interactively using the built-in topology editor.
