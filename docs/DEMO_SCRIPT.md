# BlackBoxNet — 5-Minute Demo Script

Use this for interviews, design reviews, or lab demos. **Prerequisite:** stack running (`docker-compose up -d`), browser at **http://localhost:3000**, API docs optional at **http://localhost:8000/docs**.

---

## 0:00–0:30 — One-liner + context

- **Say:** “BlackBoxNet is a network flight recorder: it stores config history in Git, metrics and events in Postgres, and replays a timeline so you can see what changed before an outage.”
- **Say:** “Phase 1 is a **deterministic simulation** — three devices, one scripted ACL mistake — so we can prove the UX and correlation without real gear.”
- **Click:** Dashboard (home).

---

## 0:30–1:30 — Healthy baseline (first step = T1)

- **Say:** “Each **Run step** snapshots the network at the current timeline, then advances time. First snapshot is **T1** — healthy baseline.”
- **Click:** **Run step** once (button may show the *next* step name, e.g. “Run T2” — that’s the step you’ll land on *after* this run completes).
- **Point:** Three device cards with metrics — **healthy** state; no incident yet.
- **Optional:** **Devices** in the nav — edge-router-1, dist-switch-1, access-switch-1.

---

## 1:30–2:30 — The mistake (second step = T2 — config change)

- **Click:** **Run step** again (this collects **T2** — ACL change on edge-router-1).
- **Say:** “Engineer replaced ACL 100 with 101 — a **deny** for 10.0.1.0/24 **before** the permit — so that subnet is blocked on the LAN interface.”
- **Point:** **CONFIG_CHANGE**-style behavior in the timeline later; Git records a new config snapshot for the router. Still no full outage until later steps.
- **Optional:** **http://localhost:8000/docs** → `POST /api/simulation/run-step` — backend is real, not browser-only.

---

## 2:30–3:30 — Degradation (T3–T4)

- **Click:** Continue **Run step** through **T3** and **T4**.
- **Say:** “Latency spikes, packet loss, interface errors, CPU rise — symptoms **downstream** of the router change.”
- **Point:** Device cards turn **degraded**; timeline events will reference dist switch and access switch, not only the router.

---

## 3:30–4:30 — Outage + incident (T5)

- **Click:** Final step to **T5** (outage).
- **Say:** “Packet loss crosses the outage threshold — we create an **incident** and link events.”
- **Click:** **Incidents** → open **“ACL Regression Blocks Downstream Subnet”**.
- **Point:** **Suspicion summary** and **correlation flags** (config before degradation, deny matches subnet, primary suspect).
- **Click:** A **CONFIG_CHANGE**-style event → **config diff** if available — show **deny rule** and interface ACL binding.

---

## 4:30–5:00 — Reset + closing

- **Click:** **Reset** on the Dashboard (simulation reset).
- **Say:** “Same run every time — deterministic — good for demos and tests.”
- **Closing:** “Phase 2 would swap the scenario engine for **real polling** (SSH/SNMP) and keep this timeline and Git model.”

---

## Quick troubleshooting (if asked)

| Symptom | Check |
|--------|--------|
| White / blank UI | Use **http://localhost:3000** (with port); ensure `web` container is up. |
| API errors in UI | `docker-compose ps`; API on **8000**; browser uses same host as Vite proxy. |
| `Not Found` on **http://localhost:8000** | Normal for `/` — use **`/docs`** or **`/api/health`**. |

---

## Optional talking points (if time)

- Git commit message format on config change: `config snapshot: <timestamp> | changed: <device>`.
- Rules-based correlation only (no ML in Phase 1) — intentional for explainability.
- Same data model supports real devices later — **CollectorService** interface stays stable.
