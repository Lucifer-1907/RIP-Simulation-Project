// ═══════════════════════════════════════════════════════════
//  RIP SIMULATOR — app.js
//  Socket.IO + vis.js Network Graph
// ═══════════════════════════════════════════════════════════

const socket = io();

// ── State ────────────────────────────────────────────────────
let network = null;
let nodesDS = null;
let edgesDS = null;
let selectedNode = null;
let autoRunning = false;
let txTotal = 0;
let rxTotal = 0;
let roundHistory = [];   // [{round, changes}] for sparkline

// ── DOM refs ─────────────────────────────────────────────────
const graphContainer = document.getElementById("network-graph");
const tableBody = document.getElementById("routing-table-body");
const logContainer = document.getElementById("log-container");
const selectedNodeName = document.getElementById("selected-node-name");
const roundDisplay = document.getElementById("round-display");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const progressBar = document.getElementById("progress-bar");
const progressPct = document.getElementById("progress-pct");
const txDisplay = document.getElementById("tx-display");
const rxDisplay = document.getElementById("rx-display");
const droppedDisplay = document.getElementById("dropped-display");

// Buttons
document.getElementById("btn-next").addEventListener("click", doNextRound);
document.getElementById("btn-auto").addEventListener("click", doAutoRun);
document.getElementById("btn-reset").addEventListener("click", doReset);
document.getElementById("btn-config").addEventListener("click", openTopologyEditor);

// Mobile nav
document.getElementById("nav-start")?.addEventListener("click", doNextRound);
document.getElementById("nav-metrics")?.addEventListener("click", showMetrics);
document.getElementById("nav-config")?.addEventListener("click", openTopologyEditor);
document.getElementById("nav-reset")?.addEventListener("click", doReset);

// ── vis.js Network Options ────────────────────────────────────
const ROUTER_IMG = new Image();
ROUTER_IMG.src = "/assets/router.png";

const PACKET_IMG = "/assets/packet.png";

const VIS_OPTIONS = {
    nodes: {
        shape: "image",
        image: "/assets/router.png",
        size: 28,
        label: "",          // set per-node in buildGraph
        font: {
            color: "#72b1ff",
            size: 13,
            face: "Space Grotesk",
            bold: { color: "#72b1ff", size: 13, face: "Space Grotesk" },
            vadjust: 8,
        },
        borderWidth: 0,
        borderWidthSelected: 2,
        color: {
            border: "#72b1ff",
            background: "transparent",
            highlight: { border: "#83fc89", background: "transparent" },
            hover: { border: "#72b1ff", background: "transparent" }
        },
        shapeProperties: { useBorderWithImage: false },
        labelHighlightBold: true,
    },
    edges: {
        color: {
            color: "rgba(114,177,255,0.25)",
            highlight: "#72b1ff",
            hover: "#72b1ff",
        },
        width: 1.5,
        smooth: { type: "dynamic" },
        hoverWidth: 3,
        selectionWidth: 3,
        arrows: { to: false },
        font: {
            color: "rgba(168,171,179,0.6)",
            size: 9,
            face: "Space Grotesk",
            align: "middle"
        }
    },
    physics: {
        enabled: true,
        stabilization: { iterations: 150 },
        barnesHut: {
            gravitationalConstant: -4000,
            springLength: 160,
            springConstant: 0.04,
            damping: 0.5,
        }
    },
    interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
    },
    layout: {
        improvedLayout: true,
    }
};

// ── Build / Rebuild Graph ─────────────────────────────────────
function buildGraph(topoData) {
    const container = document.getElementById("vis-container");
    if (!container) return;

    nodesDS = new vis.DataSet(
        topoData.nodes.map(n => ({
            id: n.id,
            label: n.id,
            title: `Router: ${n.id} — click to inspect routing table`,
        }))
    );

    edgesDS = new vis.DataSet(
        topoData.edges.map(e => ({
            id: e.id,
            from: e.from,
            to: e.to,
        }))
    );

    if (network) {
        network.destroy();
    }

    network = new vis.Network(container, { nodes: nodesDS, edges: edgesDS }, VIS_OPTIONS);

    // Node click → show routing table
    network.on("click", params => {
        if (params.nodes.length > 0) {
            const name = params.nodes[0];
            selectedNode = name;
            socket.emit("get_router_table", { name });
            if (selectedNodeName) selectedNodeName.textContent = name;
        }
    });

    // Edge click → fail link (with shift held)
    network.on("click", params => {
        if (params.edges.length > 0 && params.event.srcEvent.shiftKey) {
            const edgeId = params.edges[0];
            const edge = edgesDS.get(edgeId);
            if (edge) {
                socket.emit("fail_link", { from: edge.from, to: edge.to });
            }
        }
    });
}

// ── Node State Colors ─────────────────────────────────────────
const STATE_IMAGES = {
    default: "/assets/router.png",
    updated: "/assets/router.png",   // tinted via border glow
    converged: "/assets/router.png",
};
const STATE_BORDERS = {
    default: "#72b1ff",
    updated: "#f78166",
    converged: "#83fc89",
};

function setNodeState(nodeId, state) {
    if (!nodesDS) return;
    const border = STATE_BORDERS[state] || STATE_BORDERS.default;
    nodesDS.update({
        id: nodeId,
        color: {
            border,
            background: "transparent",
            highlight: { border, background: "transparent" },
            hover: { border, background: "transparent" },
        },
        borderWidth: state === "default" ? 0 : 2,
        borderWidthSelected: 2,
    });
}

function setEdgeState(edgeId, state) {
    if (!edgesDS) return;
    const colors = {
        idle: { color: "rgba(114,177,255,0.25)" },
        active: { color: "#72b1ff" },
        failed: { color: "#ff716c" },
    };
    const widths = { idle: 1.5, active: 3, failed: 1.5 };
    edgesDS.update({
        id: edgeId,
        color: colors[state] || colors.idle,
        width: widths[state] || 1.5,
        dashes: state === "failed" ? [6, 4] : false,
    });
}

// ── Packet Animation ──────────────────────────────────────────
function animatePackets(packets) {
    if (!network || !nodesDS) return;

    packets.forEach((pkt, idx) => {
        setTimeout(() => {
            const fromPos = network.getPositions([pkt.from])[pkt.from];
            const toPos = network.getPositions([pkt.to])[pkt.to];
            if (!fromPos || !toPos) return;

            const canvas = document.querySelector("#vis-container canvas");
            if (!canvas) return;

            // Animate a glowing dot on the canvas overlay
            const overlay = document.getElementById("packet-overlay");
            if (!overlay) return;

            const dot = document.createElement("img");
            dot.src = PACKET_IMG;
            dot.className = "packet-dot";
            dot.style.width = "20px";
            dot.style.height = "20px";
            overlay.appendChild(dot);

            const rect = canvas.getBoundingClientRect();

            // Convert vis coords to screen coords
            function visToScreen(pos) {
                const domPos = network.canvasToDOM(pos);
                return {
                    x: domPos.x,
                    y: domPos.y,
                };
            }

            const start = visToScreen(fromPos);
            const end = visToScreen(toPos);

            dot.style.left = `${start.x}px`;
            dot.style.top = `${start.y}px`;

            const duration = 600; // ms
            const startTime = performance.now();

            function step(now) {
                const t = Math.min((now - startTime) / duration, 1);
                const ease = t * t * (3 - 2 * t); // smoothstep
                dot.style.left = `${start.x + (end.x - start.x) * ease}px`;
                dot.style.top = `${start.y + (end.y - start.y) * ease}px`;
                if (t < 1) {
                    requestAnimationFrame(step);
                } else {
                    dot.remove();
                }
            }
            requestAnimationFrame(step);
        }, idx * 25);
    });
}

// ── Routing Table Render ──────────────────────────────────────
function renderTable(tableRows) {
    if (!tableBody) return;
    tableBody.innerHTML = "";
    tableRows.forEach(row => {
        const isInf = row.metric >= 16;
        const isDrop = row.next_hop === "DROP" || isInf;
        const tr = document.createElement("tr");
        tr.className = "hover:bg-primary/5 group transition-colors";
        tr.innerHTML = `
            <td class="px-4 py-3 font-bold ${isDrop ? "text-error" : "text-primary"}">${row.dest}</td>
            <td class="px-4 py-3 text-on-surface-variant">${row.next_hop}</td>
            <td class="px-4 py-3 text-right font-mono ${isDrop ? "text-error" : "text-secondary"}">${isInf ? "INF" : String(row.metric).padStart(2, "0")}</td>
        `;
        tableBody.appendChild(tr);
    });
}

// ── Log Render ────────────────────────────────────────────────
const LOG_COLORS = {
    ROUTING: "text-primary",
    SUCCESS: "text-secondary",
    WARNING: "text-tertiary-dim",
    SYSTEM: "text-on-surface",
    ERROR: "text-error",
};

function appendLog(level, msg) {
    if (!logContainer) return;
    const now = new Date();
    const time = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;
    const cls = LOG_COLORS[level] || "text-on-surface-variant";

    const p = document.createElement("p");
    p.className = "mb-1";
    p.innerHTML = `<span class="text-on-surface-variant/40">[${time}]</span> <span class="${cls}">${level}:</span> ${msg}`;
    logContainer.appendChild(p);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// ── Stats / Progress ──────────────────────────────────────────
function updateStats(stats) {
    if (roundDisplay) roundDisplay.textContent = String(stats.round).padStart(3, "0");
    if (txDisplay) txDisplay.textContent = stats.tx.toLocaleString();
    if (rxDisplay) rxDisplay.textContent = stats.rx.toLocaleString();
    if (droppedDisplay) droppedDisplay.textContent = stats.dropped.toLocaleString();

    const pct = stats.progress ?? 0;
    if (progressBar) progressBar.style.width = `${pct}%`;
    if (progressPct) progressPct.textContent = `${pct}%`;

    if (stats.converged) {
        setStatus("STABLE", true);
    } else {
        setStatus("RUNNING", false);
    }
}

function setStatus(label, converged) {
    if (statusDot) {
        statusDot.className = converged
            ? "w-2 h-2 rounded-full bg-secondary shadow-[0_0_8px_#83fc89]"
            : "w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_#ff9880] animate-pulse";
    }
    if (statusText) {
        statusText.textContent = label;
        statusText.className = converged ? "text-[10px] uppercase tracking-widest text-secondary font-bold"
            : "text-[10px] uppercase tracking-widest text-tertiary font-bold";
    }
}

// ── Button Actions ────────────────────────────────────────────
function doNextRound() {
    socket.emit("next_round");
}

function doAutoRun() {
    autoRunning = !autoRunning;
    const btn = document.getElementById("btn-auto");
    if (autoRunning) {
        if (btn) { btn.textContent = "STOP"; btn.classList.add("text-error"); }
        socket.emit("auto_run");
    } else {
        if (btn) { btn.textContent = "AUTO_RUN"; btn.classList.remove("text-error"); }
        // auto_run is server-side; reset stops it on next reset
    }
}

function doReset() {
    autoRunning = false;
    const btn = document.getElementById("btn-auto");
    if (btn) { btn.textContent = "AUTO_RUN"; btn.classList.remove("text-error"); }
    roundHistory = [];
    socket.emit("reset");
}

function showMetrics() {
    // Scroll to stats footer on mobile
    document.querySelector("footer")?.scrollIntoView({ behavior: "smooth" });
}

// ── Topology Editor ──────────────────────────────────────────
// Internal state for the editor
let _topoRouters = [];   // ["R1","R2",...]
let _topoLinks = [];   // [{from:"R1",to:"R2"},...]

function openTopologyEditor() {
    // Pre-populate from current live topology
    _topoRouters = nodesDS ? nodesDS.getIds().map(String).sort() : [];
    _topoLinks = edgesDS ? edgesDS.get().map(e => ({ from: e.from, to: e.to })) : [];

    _topoRenderRouters();
    _topoRenderLinks();
    _topoRefreshDropdowns();

    document.getElementById("topo-modal").classList.remove("hidden");
}

function closeTopologyEditor() {
    document.getElementById("topo-modal").classList.add("hidden");
}

function _topoRenderRouters() {
    const lb = document.getElementById("router-list");
    lb.innerHTML = "";
    _topoRouters.forEach(r => {
        const opt = document.createElement("option");
        opt.value = r;
        opt.textContent = r;
        opt.style.padding = "4px 8px";
        lb.appendChild(opt);
    });
}

function _topoRenderLinks() {
    const lb = document.getElementById("link-list");
    lb.innerHTML = "";
    _topoLinks.forEach((l, i) => {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = `${l.from}  ──  ${l.to}`;
        opt.style.padding = "4px 8px";
        lb.appendChild(opt);
    });
}

function _topoRefreshDropdowns() {
    const fromSel = document.getElementById("link-from");
    const toSel = document.getElementById("link-to");
    const prev = { from: fromSel.value, to: toSel.value };

    fromSel.innerHTML = "";
    toSel.innerHTML = "";

    _topoRouters.forEach(r => {
        fromSel.innerHTML += `<option value="${r}">${r}</option>`;
        toSel.innerHTML += `<option value="${r}">${r}</option>`;
    });

    if (prev.from) fromSel.value = prev.from;
    if (prev.to) toSel.value = prev.to;
}

function topoAddRouter() {
    const input = document.getElementById("new-router-input");
    const name = input.value.trim().toUpperCase();
    if (!name) return;
    if (_topoRouters.includes(name)) {
        appendLog("WARNING", `Router '${name}' already exists.`);
        return;
    }
    _topoRouters.push(name);
    _topoRouters.sort();
    input.value = "";
    _topoRenderRouters();
    _topoRefreshDropdowns();
}

function topoRemoveRouter() {
    const lb = document.getElementById("router-list");
    const sel = [...lb.selectedOptions].map(o => o.value);
    if (!sel.length) return;
    sel.forEach(name => {
        _topoRouters = _topoRouters.filter(r => r !== name);
        _topoLinks = _topoLinks.filter(l => l.from !== name && l.to !== name);
    });
    _topoRenderRouters();
    _topoRenderLinks();
    _topoRefreshDropdowns();
}

function topoAddLink() {
    const from = document.getElementById("link-from").value;
    const to = document.getElementById("link-to").value;
    if (!from || !to) return;
    if (from === to) {
        appendLog("WARNING", "A router cannot link to itself.");
        return;
    }
    // check duplicate
    const exists = _topoLinks.some(l =>
        (l.from === from && l.to === to) || (l.from === to && l.to === from)
    );
    if (exists) {
        appendLog("WARNING", `Link ${from} ── ${to} already exists.`);
        return;
    }
    _topoLinks.push({ from, to });
    _topoRenderLinks();
}

function topoRemoveLink() {
    const lb = document.getElementById("link-list");
    const sel = [...lb.selectedOptions].map(o => parseInt(o.value));
    if (!sel.length) return;
    _topoLinks = _topoLinks.filter((_, i) => !sel.includes(i));
    _topoRenderLinks();
}

function submitTopology() {
    if (_topoRouters.length < 2) {
        appendLog("WARNING", "Add at least 2 routers.");
        return;
    }
    if (_topoLinks.length === 0) {
        appendLog("WARNING", "Add at least one link.");
        return;
    }
    socket.emit("set_topology", { nodes: _topoRouters, edges: _topoLinks });
    closeTopologyEditor();
}

// ── Socket Events ─────────────────────────────────────────────
socket.on("connect", () => {
    appendLog("SYSTEM", "Socket connected.");
});

socket.on("topology", data => {
    buildGraph(data);
    appendLog("SYSTEM", `Topology: ${data.nodes.length} routers, ${data.edges.length} links.`);
});

socket.on("tables", data => {
    // If a router is selected, update its table view
    if (selectedNode && data[selectedNode]) {
        renderTable(data[selectedNode]);
    }
});

socket.on("stats", data => {
    updateStats(data);
});

socket.on("animate_packets", data => {
    // Highlight active edges
    data.active_edges?.forEach(eid => {
        setEdgeState(eid, "active");
        setTimeout(() => setEdgeState(eid, "idle"), 800);
    });
    animatePackets(data.packets || []);
});

socket.on("round_result", data => {
    updateStats(data.stats);

    // Color changed nodes orange, then back
    if (nodesDS) {
        data.changed?.forEach(name => {
            setNodeState(name, "updated");
            setTimeout(() => {
                setNodeState(name, data.converged ? "converged" : "default");
            }, 1200);
        });

        if (data.converged) {
            Object.keys(data.tables || {}).forEach(n => setNodeState(n, "converged"));
        }
    }

    // Update routing table if node selected
    if (selectedNode && data.tables?.[selectedNode]) {
        renderTable(data.tables[selectedNode]);
    }

    roundHistory.push({ round: data.round, changes: data.changed?.length || 0 });
});

socket.on("router_table", data => {
    renderTable(data.table);
    if (selectedNodeName) selectedNodeName.textContent = data.name;
});

socket.on("log", data => {
    appendLog(data.level, data.msg);
});

socket.on("reset_done", () => {
    if (nodesDS) {
        nodesDS.getIds().forEach(id => setNodeState(id, "default"));
    }
    if (tableBody) tableBody.innerHTML = "";
    if (selectedNodeName) selectedNodeName.textContent = "—";
    selectedNode = null;
    appendLog("SYSTEM", "Simulation reset complete.");
});

socket.on("link_failed", data => {
    setEdgeState(data.edge_id, "failed");
    appendLog("ERROR", `Link ${data.edge_id.replace("-", " <-> ")} is DOWN.`);
});