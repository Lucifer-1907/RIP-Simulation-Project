from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import os, time

from network_topology import load_topology
from rip_algorithm import run_rip_round
from router import Router

app = Flask(__name__)
app.config["SECRET_KEY"] = "rip-sim-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
TOPOLOGY_FILE = os.path.join(BASE_DIR, "data", "topology.txt")

routers      = {}
round_number = 0
converged    = False
tx_packets   = 0
rx_packets   = 0
dropped      = 0

def _load():
    global routers, round_number, converged, tx_packets, rx_packets, dropped
    routers      = load_topology(TOPOLOGY_FILE)
    round_number = 0
    converged    = False
    tx_packets   = 0
    rx_packets   = 0
    dropped      = 0

_load()

# ── helpers ──────────────────────────────────────────────────

def _topology_payload():
    nodes = []
    for name in routers:
        nodes.append({"id": name, "label": name})

    edges, seen = [], set()
    for name, r in routers.items():
        for nb in r.neighbors:
            edge = tuple(sorted((name, nb.name)))
            if edge not in seen:
                seen.add(edge)
                edges.append({"from": edge[0], "to": edge[1],
                               "id": f"{edge[0]}-{edge[1]}"})
    return {"nodes": nodes, "edges": edges}

def _tables_payload():
    return {
        name: [
            {"dest": d, "next_hop": nh if nh else "-", "metric": m}
            for d, (nh, m) in sorted(r.get_routing_table().items())
        ]
        for name, r in routers.items()
    }

def _stats_payload():
    progress = 0
    if routers and round_number > 0:
        # estimate convergence as fraction of round_number vs expected
        expected = max(len(routers) - 1, 1)
        progress = min(int((round_number / expected) * 100), 99)
    if converged:
        progress = 100
    return {
        "tx": tx_packets,
        "rx": rx_packets,
        "dropped": dropped,
        "progress": progress,
        "round": round_number,
        "converged": converged,
    }

# ── routes ───────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    assets_dir = os.path.join(BASE_DIR, "assets")
    return send_from_directory(assets_dir, filename)

# ── socket events ────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    emit("topology",  _topology_payload())
    emit("tables",    _tables_payload())
    emit("stats",     _stats_payload())
    emit("log", {"level": "SYSTEM",
                 "msg": f"Connected — {len(routers)} routers loaded."})

@socketio.on("get_topology")
def on_get_topology():
    emit("topology", _topology_payload())

@socketio.on("next_round")
def on_next_round():
    global round_number, converged, tx_packets, rx_packets, dropped

    if converged:
        emit("log", {"level": "SYSTEM", "msg": "Network already converged."})
        return

    round_number += 1

    # Build packet list for animation
    messages = []
    for rname, router in routers.items():
        snap = router.get_routing_table()
        for nb in router.neighbors:
            messages.append({"sender": rname, "receiver": nb.name, "table": snap})

    n = len(messages)
    tx_packets += n
    rx_packets += n     # in RIP all packets delivered

    active_edges = [
        tuple(sorted((m["sender"], m["receiver"]))) for m in messages
    ]
    emit("animate_packets", {
        "packets": [{"from": m["sender"], "to": m["receiver"]} for m in messages],
        "active_edges": [f"{e[0]}-{e[1]}" for e in set(active_edges)]
    })

    # Run the algorithm
    conv, updates = run_rip_round(routers)
    converged = conv

    changed = set()
    for msg in updates:
        parts = msg.split()
        if parts:
            changed.add(parts[0])
        emit("log", {"level": "ROUTING", "msg": msg})

    if not updates:
        emit("log", {"level": "ROUTING",
                     "msg": f"Round {round_number}: No changes detected."})

    emit("round_result", {
        "round":    round_number,
        "converged": converged,
        "changed":  list(changed),
        "tables":   _tables_payload(),
        "stats":    _stats_payload(),
    })

    if converged:
        emit("log", {"level": "SUCCESS",
                     "msg": f"CONVERGENCE reached after {round_number} round(s)!"})

@socketio.on("auto_run")
def on_auto_run():
    """Server-side auto-run: fires rounds until converged."""
    global converged
    if converged:
        return
    while not converged:
        on_next_round()
        socketio.sleep(1.5)

@socketio.on("reset")
def on_reset():
    _load()
    emit("topology", _topology_payload())
    emit("tables",   _tables_payload())
    emit("stats",    _stats_payload())
    emit("log", {"level": "SYSTEM", "msg": "Simulation reset."})
    emit("reset_done")

@socketio.on("set_topology")
def on_set_topology(data):
    """Receive custom topology from frontend editor."""
    global routers, round_number, converged, tx_packets, rx_packets, dropped
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if len(nodes) < 2 or not edges:
        emit("log", {"level": "WARNING",
                     "msg": "Need at least 2 nodes and 1 edge."})
        return
    routers = {n: Router(n) for n in nodes}
    for e in edges:
        a, b = e["from"], e["to"]
        if a in routers and b in routers:
            routers[a].add_neighbor(routers[b])
            routers[b].add_neighbor(routers[a])
    round_number = 0
    converged    = False
    tx_packets   = 0
    rx_packets   = 0
    dropped      = 0
    emit("topology", _topology_payload())
    emit("tables",   _tables_payload())
    emit("stats",    _stats_payload())
    emit("log", {"level": "SYSTEM",
                 "msg": f"New topology loaded: {len(routers)} routers."})

@socketio.on("fail_link")
def on_fail_link(data):
    """Cut a link between two routers mid-simulation."""
    a, b = data.get("from"), data.get("to")
    if a not in routers or b not in routers:
        return
    ra, rb = routers[a], routers[b]
    ra.neighbors = [n for n in ra.neighbors if n.name != b]
    rb.neighbors = [n for n in rb.neighbors if n.name != a]
    emit("log", {"level": "WARNING",
                 "msg": f"Link FAILED: {a} <-> {b} disconnected."})
    emit("link_failed", {"edge_id": f"{min(a,b)}-{max(a,b)}"})

@socketio.on("get_router_table")
def on_get_router_table(data):
    name = data.get("name")
    if name not in routers:
        return
    table = [
        {"dest": d, "next_hop": nh if nh else "-", "metric": m}
        for d, (nh, m) in sorted(routers[name].get_routing_table().items())
    ]
    emit("router_table", {"name": name, "table": table})

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)