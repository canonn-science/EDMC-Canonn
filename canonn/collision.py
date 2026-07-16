"""
3D Keplerian collision prediction, ported from canonn-signals'
`orbital-relations.core.ts`. Replaces the old close_flypast() heuristic
(apoapsis/periapsis-only, 2D, no phase check) with a real 3D orbit-plane
crossing test plus a predicted contact date/window.

This is deliberately run off the Tkinter thread (see CollisionCalculator)
and is cancellable via a threading.Event, since the coarse-grid + zoom-refine
search is O(N^2) per sibling pair and can take a noticeable amount of wall
time in pure Python.
"""

import heapq
import math
import re
import threading
import time
from datetime import datetime, timezone

from canonn.debug import Debug

AU_KM = 149597870.7

# Sampling constants. The reference TypeScript implementation runs in a Web
# Worker on a JS engine and uses larger sample counts (720 coarse orbit
# samples, 2000 conjunction-scan samples, up to 300 conjunctions). We keep
# the same coarse orbit sampling (cheap) but cap the conjunction march lower
# since CPython is much slower at this than V8 and this still needs to
# finish in a background thread within a reasonable time.
ORBIT_COARSE_SAMPLES = 720
ORBIT_REFINE_TOPK = 6
ORBIT_REFINE_GRID = 4
ORBIT_REFINE_ITERATIONS = 10

CONJUNCTION_SCAN_SAMPLES = 2000
CONJUNCTION_REFINE_SAMPLES = 500
MAX_CONJUNCTIONS_SCANNED = 60
EDGE_STEP_MS = 30_000.0
EDGE_BISECT_ITERATIONS = 40


def _clamp_eccentricity(e):
    return max(0.0, min(0.999, e))


def _solve_kepler(mean_anomaly_rad, e):
    e = _clamp_eccentricity(e)
    E = mean_anomaly_rad if e < 0.8 else math.pi
    for _ in range(12):
        delta = (E - e * math.sin(E) - mean_anomaly_rad) / (1 - e * math.cos(E))
        E -= delta
        if abs(delta) < 1e-12:
            break
    return E


def orbital_state_vector(a_au, e, argp_deg, inc_deg, node_deg, mean_anomaly_deg):
    """3D position (km) of a body at a given mean anomaly, ED sign convention."""
    e = _clamp_eccentricity(e)
    M = math.radians(mean_anomaly_deg % 360.0)
    E = _solve_kepler(M, e)

    a_km = a_au * AU_KM
    x_o = a_km * (math.cos(E) - e)
    y_o = a_km * math.sqrt(1 - e * e) * math.sin(E)

    # ED/Spansh ascendingNode and argOfPeriapsis are the opposite sign from
    # the standard astronomical frame.
    node = -math.radians(node_deg)
    argp = -math.radians(argp_deg)
    inc = math.radians(inc_deg)

    cn, sn = math.cos(node), math.sin(node)
    ca, sa = math.cos(argp), math.sin(argp)
    ci, si = math.cos(inc), math.sin(inc)

    x = x_o * (cn * ca - sn * sa * ci) - y_o * (cn * sa + sn * ca * ci)
    y = x_o * (sn * ca + cn * sa * ci) - y_o * (sn * sa - cn * ca * ci)
    z = x_o * (sa * si) + y_o * (ca * si)
    return (x, y, z)


def _normalize(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0:
        return v
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(u, v):
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _dot(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _dist2(a, b):
    dx, dy, dz = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return dx * dx + dy * dy + dz * dz


def min_orbit_distance_km(candidate_a, candidate_b, cancel_event):
    """
    Minimum distance (km) between the two orbit *curves*, independent of
    where each body currently sits in its orbit. Returns None if cancelled.
    """
    step_deg = 360.0 / ORBIT_COARSE_SAMPLES
    pos_a = [
        orbital_state_vector(
            candidate_a["a"], candidate_a["e"], candidate_a["argp"],
            candidate_a["inc"], candidate_a["node"], i * step_deg,
        )
        for i in range(ORBIT_COARSE_SAMPLES)
    ]
    pos_b = [
        orbital_state_vector(
            candidate_b["a"], candidate_b["e"], candidate_b["argp"],
            candidate_b["inc"], candidate_b["node"], j * step_deg,
        )
        for j in range(ORBIT_COARSE_SAMPLES)
    ]

    heap = []
    for i, pa in enumerate(pos_a):
        if cancel_event.is_set():
            return None
        for j, pb in enumerate(pos_b):
            d2 = _dist2(pa, pb)
            if len(heap) < ORBIT_REFINE_TOPK:
                heapq.heappush(heap, (-d2, i, j))
            elif -d2 > heap[0][0]:
                heapq.heapreplace(heap, (-d2, i, j))

    seeds = [(i, j) for (_, i, j) in heap]

    # Line-of-nodes seeding: near-coplanar, closely-nested orbits approach
    # only in a sliver around their mutual node that the coarse grid alone
    # can miss.
    quarter = ORBIT_COARSE_SAMPLES // 4
    normal_a = _normalize(_cross(pos_a[0], pos_a[quarter]))
    normal_b = _normalize(_cross(pos_b[0], pos_b[quarter]))
    node_line = _cross(normal_a, normal_b)
    node_line_len = math.sqrt(_dot(node_line, node_line))
    if node_line_len > 1e-9:
        node_line = _normalize(node_line)
        norm_a_units = [_normalize(p) for p in pos_a]
        norm_b_units = [_normalize(p) for p in pos_b]
        for direction in (node_line, tuple(-c for c in node_line)):
            best_i = max(range(ORBIT_COARSE_SAMPLES), key=lambda i: _dot(norm_a_units[i], direction))
            best_j = max(range(ORBIT_COARSE_SAMPLES), key=lambda j: _dot(norm_b_units[j], direction))
            seeds.append((best_i, best_j))

    best_overall = math.inf
    for (i0, j0) in seeds:
        if cancel_event.is_set():
            return None
        ma, mb = i0 * step_deg, j0 * step_deg
        step = step_deg
        for _pass in range(ORBIT_REFINE_ITERATIONS):
            local_best = math.inf
            local_ma, local_mb = ma, mb
            for di in range(-ORBIT_REFINE_GRID, ORBIT_REFINE_GRID + 1):
                cand_ma = ma + di * step
                pa = orbital_state_vector(
                    candidate_a["a"], candidate_a["e"], candidate_a["argp"],
                    candidate_a["inc"], candidate_a["node"], cand_ma,
                )
                for dj in range(-ORBIT_REFINE_GRID, ORBIT_REFINE_GRID + 1):
                    cand_mb = mb + dj * step
                    pb = orbital_state_vector(
                        candidate_b["a"], candidate_b["e"], candidate_b["argp"],
                        candidate_b["inc"], candidate_b["node"], cand_mb,
                    )
                    d2 = _dist2(pa, pb)
                    if d2 < local_best:
                        local_best, local_ma, local_mb = d2, cand_ma, cand_mb
            ma, mb = local_ma, local_mb
            step /= 2.0
            if local_best < best_overall:
                best_overall = local_best

    return math.sqrt(best_overall)


def _position_at_time(candidate, t_ms):
    days_elapsed = (t_ms - candidate["epoch_ms"]) / 86400000.0
    mean_anomaly = candidate["mean_anomaly0"] + (days_elapsed / candidate["period"]) * 360.0
    return orbital_state_vector(
        candidate["a"], candidate["e"], candidate["argp"],
        candidate["inc"], candidate["node"], mean_anomaly,
    )


def separation_km(candidate_a, candidate_b, t_ms):
    pa = _position_at_time(candidate_a, t_ms)
    pb = _position_at_time(candidate_b, t_ms)
    return math.sqrt(_dist2(pa, pb))


def synodic_days(candidate_a, candidate_b):
    try:
        return 1.0 / abs(1.0 / candidate_a["period"] - 1.0 / candidate_b["period"])
    except ZeroDivisionError:
        return math.inf


def _find_window_edge(candidate_a, candidate_b, contact_km, t_min, step_sign, bound_ms, cancel_event):
    """Root-find the start (step_sign=-1) or end (step_sign=+1) of a contact
    window: walk in EDGE_STEP_MS steps while still in contact, then bisect."""
    x_in = 0.0
    while True:
        if cancel_event.is_set():
            return t_min + step_sign * x_in
        x_out = x_in + EDGE_STEP_MS
        if x_out > bound_ms:
            return t_min + step_sign * x_out
        t_out = t_min + step_sign * x_out
        if separation_km(candidate_a, candidate_b, t_out) <= contact_km:
            x_in = x_out
            continue
        lo, hi = x_in, x_out
        for _ in range(EDGE_BISECT_ITERATIONS):
            mid = (lo + hi) / 2.0
            t_mid = t_min + step_sign * mid
            if separation_km(candidate_a, candidate_b, t_mid) <= contact_km:
                lo = mid
            else:
                hi = mid
        return t_min + step_sign * lo


def _refine_minimum(candidate_a, candidate_b, center_ms, half_window_ms, samples, cancel_event):
    best_t, best_sep = center_ms, separation_km(candidate_a, candidate_b, center_ms)
    window = half_window_ms
    while window >= 500.0:
        if cancel_event.is_set():
            return best_t, best_sep
        step = (2 * window) / (samples - 1) if samples > 1 else 0
        start = best_t - window
        local_best_t, local_best_sep = best_t, best_sep
        for k in range(samples):
            t = start + k * step
            sep = separation_km(candidate_a, candidate_b, t)
            if sep < local_best_sep:
                local_best_sep, local_best_t = sep, t
        best_t, best_sep = local_best_t, local_best_sep
        window /= 2.0
    return best_t, best_sep


def next_contacts(candidate_a, candidate_b, now_ms, contact_km, cancel_event, count=1):
    """
    Predicted contact window(s): {start_ms, end_ms, days, min_separation_km,
    combined_radii_km}, soonest first. Returns [] if the pair never comes
    within contact_km, None if cancelled mid-search.
    """
    syn_days = synodic_days(candidate_a, candidate_b)
    syn_ms = syn_days * 86400000.0
    if not math.isfinite(syn_ms) or syn_ms <= 0:
        return []

    scan_start = now_ms - 0.5 * syn_ms
    scan_end = now_ms + 1.0 * syn_ms
    step = (scan_end - scan_start) / (CONJUNCTION_SCAN_SAMPLES - 1)
    best_t, best_sep = scan_start, math.inf
    for k in range(CONJUNCTION_SCAN_SAMPLES):
        if cancel_event.is_set():
            return None
        t = scan_start + k * step
        sep = separation_km(candidate_a, candidate_b, t)
        if sep < best_sep:
            best_sep, best_t = sep, t

    best_t, best_sep = _refine_minimum(
        candidate_a, candidate_b, best_t, step, CONJUNCTION_SCAN_SAMPLES, cancel_event
    )
    if cancel_event.is_set():
        return None

    # Anchor: the most recent conjunction strictly before now.
    t0 = best_t
    while t0 >= now_ms:
        t0 -= syn_ms

    contacts = []
    for k in range(MAX_CONJUNCTIONS_SCANNED):
        if cancel_event.is_set():
            return None
        if len(contacts) >= count:
            break
        t_k = t0 + k * syn_ms
        c_best_t, c_best_sep = _refine_minimum(
            candidate_a, candidate_b, t_k, syn_ms / 4.0, CONJUNCTION_REFINE_SAMPLES, cancel_event
        )
        if cancel_event.is_set():
            return None
        if c_best_sep > contact_km:
            continue
        if c_best_t < now_ms - syn_ms / 2.0:
            continue
        if contacts and c_best_t <= contacts[-1]["end_ms"]:
            continue

        bound_ms = syn_ms / 2.0
        start_ms = _find_window_edge(candidate_a, candidate_b, contact_km, c_best_t, -1, bound_ms, cancel_event)
        end_ms = _find_window_edge(candidate_a, candidate_b, contact_km, c_best_t, 1, bound_ms, cancel_event)
        if end_ms < now_ms:
            continue

        contacts.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "days": (start_ms - now_ms) / 86400000.0,
            "min_separation_km": c_best_sep,
            "combined_radii_km": contact_km,
        })

    return contacts


_TS_RE = re.compile(r"([+-]\d{2}):?(\d{2})?$")


def _parse_epoch_ms(ts):
    if not ts:
        return None
    s = str(ts).strip().replace("T", " ")
    if s.endswith("Z"):
        s = s[:-1]
        try:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            return dt.timestamp() * 1000.0
        except ValueError:
            return None

    m = _TS_RE.search(s)
    if m:
        minutes = m.group(2) or "00"
        s = s[: m.start()] + m.group(1) + minutes
        try:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S%z")
            return dt.timestamp() * 1000.0
        except ValueError:
            return None

    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.timestamp() * 1000.0
    except ValueError:
        return None


def _radius_km(body):
    if body.get("type") == "Star":
        solar_radius = body.get("solarRadius")
        if solar_radius is None:
            return None
        return solar_radius * 695500.0
    return body.get("radius")


def _build_candidate(body):
    if body.get("type") not in ("Planet", "Star"):
        return None
    if not body.get("parents"):
        return None

    a = body.get("semiMajorAxis")
    e = body.get("orbitalEccentricity")
    period = body.get("orbitalPeriod")
    inc = body.get("orbitalInclination")
    argp = body.get("argOfPeriapsis")
    node = body.get("ascendingNode")
    mean_anomaly = body.get("meanAnomaly")

    if None in (a, e, period, inc, argp, node, mean_anomaly):
        return None
    if a <= 0 or e < 0 or e >= 1 or not period:
        return None

    epoch_ms = _parse_epoch_ms(body.get("updateTime"))
    if epoch_ms is None:
        return None

    radius_km = _radius_km(body)
    if not radius_km:
        return None

    return {
        "id": body.get("bodyId"),
        "parent_key": str(body.get("parents")[0]),
        "a": a,
        "e": e,
        "inc": inc,
        "argp": argp,
        "node": node,
        "period": period,
        "mean_anomaly0": mean_anomaly,
        "epoch_ms": epoch_ms,
        "radius_km": radius_km,
    }


def compute_system_collisions(bodies, now_ms, cancel_event, count=1):
    """
    bodies: dict of bodyId -> body dict (same shape as CodexTypes.bodies).
    Returns dict of bodyId -> [contact dict, ...] (each with a "partner_id"
    key added), or None if cancelled before completion.
    """
    candidates = {}
    for body_id, body in bodies.items():
        candidate = _build_candidate(body)
        if candidate:
            candidates[body_id] = candidate

    groups = {}
    for body_id, candidate in candidates.items():
        groups.setdefault(candidate["parent_key"], []).append(body_id)

    results = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        for idx_a in range(len(members)):
            for idx_b in range(idx_a + 1, len(members)):
                if cancel_event.is_set():
                    return None

                id_a, id_b = members[idx_a], members[idx_b]
                cand_a, cand_b = candidates[id_a], candidates[id_b]

                # Step 0.1: equal periods are stable co-orbital
                # configurations (Trojans/rosettes) - never lap each other.
                if abs(cand_a["period"] - cand_b["period"]) < 1e-6:
                    continue

                # Step 0.2: radial band overlap (cheap pre-filter).
                peri_a, apo_a = cand_a["a"] * (1 - cand_a["e"]), cand_a["a"] * (1 + cand_a["e"])
                peri_b, apo_b = cand_b["a"] * (1 - cand_b["e"]), cand_b["a"] * (1 + cand_b["e"])
                contact_km = cand_a["radius_km"] + cand_b["radius_km"]
                if max(peri_a, peri_b) - min(apo_a, apo_b) > contact_km / AU_KM:
                    continue

                # Step 0.3: exact 3D orbit-curve minimum distance.
                min_dist = min_orbit_distance_km(cand_a, cand_b, cancel_event)
                if min_dist is None:
                    return None
                if min_dist > contact_km:
                    continue

                contacts = next_contacts(cand_a, cand_b, now_ms, contact_km, cancel_event, count=count)
                if contacts is None:
                    return None
                if not contacts:
                    continue

                contact = contacts[0]
                results.setdefault(id_a, []).append(dict(contact, partner_id=id_b))
                results.setdefault(id_b, []).append(dict(contact, partner_id=id_a))

    return results


class CollisionCalculator(threading.Thread):
    """Background thread wrapper, matching the codexName/poiTypes pattern
    already used elsewhere in codex.py. Cancel via the shared cancel_event
    (e.g. on system change or plugin shutdown) - the coarse-grid search
    checks it frequently and bails out promptly."""

    def __init__(self, bodies, cancel_event, callback, count=1):
        threading.Thread.__init__(self, daemon=True)
        self.bodies = bodies
        self.cancel_event = cancel_event
        self.callback = callback
        self.count = count

    def run(self):
        now_ms = time.time() * 1000.0
        try:
            results = compute_system_collisions(
                self.bodies, now_ms, self.cancel_event, count=self.count
            )
        except Exception as e:
            Debug.logger.error("Error computing collision predictions")
            Debug.logger.exception(e)
            results = None

        if results is not None and not self.cancel_event.is_set():
            self.callback(results)
