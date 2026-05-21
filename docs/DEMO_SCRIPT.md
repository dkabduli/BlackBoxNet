# BlackBoxNet — 5-Minute Demo Script

Use this for interviews, design reviews, or lab demos.

**Local prerequisite:** stack running (`docker-compose up -d`), browser at **http://localhost:3000**, API docs optional at **http://localhost:8000/docs**.

**Public demo:** deploy via [DEPLOY_RENDER.md](./DEPLOY_RENDER.md). Tell viewers the free API may take **30–60s** to wake on the first click after idle.

---

## 0:00–0:30 — One-liner + context

- **Say:** “BlackBoxNet is a network flight recorder: it stores config history in Git, metrics and events in Postgres, and replays a timeline so you can see what changed before an outage.”
- **Say:** “Phase 1 is a **deterministic simulation** — three devices, one scripted ACL mistake — so we can prove the UX and correlation without real gear.”
- **Optional Phase 1.5 line:** “One device can now provide a real running-config over SSH while the rest of the outage remains simulated, so the same Git/diff/timeline flow works on a live artifact too.”
- **Click:** Dashboard (home).

---

## 0:30–1:30 — Healthy baseline (first step = T1)

- **Say:** “Each **Run T-step** snapshots the network at the current checkpoint. I’m replaying one path: users on `10.0.1.0/24` through access, distribution, and the edge router.”
- **Click:** **Run T1** once.
- **Point:** Topology preview with ports and subnet labels; three device cards in **healthy** state; no incident yet.
- **If enabled:** Point out the `live ssh config` badge on the real-device card.
- **Optional:** **Devices** in the nav — edge-router-1, dist-switch-1, access-switch-1.

---

## 1:30–2:30 — The mistake (second step = T2 — config change)

- **Click:** **Run T2** (ACL change on edge-router-1).
- **Say:** “Engineer replaced ACL 100 with 101 — a **deny** for 10.0.1.0/24 **before** the permit — so that subnet is blocked on the LAN interface.”
- **Point:** **CONFIG_CHANGE**-style behavior in the timeline later; Git records a new config snapshot for the router. Still no full outage until later steps.
- **Optional:** **http://localhost:8000/docs** → `POST /api/simulation/run-step` — backend is real, not browser-only.

---

## 2:30–3:30 — Degradation (T3–T4)

- **Click:** Continue through **Run T3** and **Run T4**.
- **Say:** “Latency spikes, packet loss, interface errors, CPU rise — symptoms **downstream** of the router change.”
- **Point:** Device cards turn **degraded**; timeline events will reference dist switch and access switch, not only the router.

---

## 3:30–4:30 — Outage + incident (T5)

- **Click:** Final step to **T5** (outage).
- **Say:** “Packet loss crosses the outage threshold — we create an **incident** and link events.”
- **Click:** **Incidents** → open **“ACL Regression Blocks Downstream Subnet”**.
- **Point:** **Suspicion summary**, **correlation flags**, and the direct **Root Cause Config Mismatch** panel.
- **Click:** **View Root Cause Diff** — show the deny rule and interface ACL binding.
- **If enabled:** Point out the `live ssh source` / `secrets redacted` badges in the diff modal.

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
| No incident shown | Run all steps from **T1** through **T5**; the outage incident is only created once **T5** is collected. |
| Real device step fails | Check `REAL_DEVICE_*` env vars, network reachability, SSH auth, and whether the target accepts `show running-config`. |

---

## Optional talking points (if time)

- Git commit message format on config change: `config snapshot: <timestamp> | changed: <device>`.
- Rules-based correlation only (no ML in Phase 1) — intentional for explainability.
- Same data model supports real devices later — **CollectorService** interface stays stable.

---

## Quick multi-vendor demo (12 scenarios, ~3 min)

Use the **public web URL** from [DEPLOY_RENDER.md](./DEPLOY_RENDER.md). Wait through the first cold-start **Run T1** if needed.

1. **Cisco** (default) → **ACL Regression** → Run **T1→T5** → open incident → **View Root Cause Diff**.
2. Header **Juniper** → confirm reset dialog if prompted → **BGP Hold Timer** → Run **T1→T5** → point at topology (hold-time annotation).
3. Header **Nokia** → **LDP Collision** → Run **T1→T5** → show LFIB / label collision in correlation or diff.
4. Mention: twelve isolated scenarios in Postgres; Git configs seeded on API boot; free tier API sleep ~15 min.
