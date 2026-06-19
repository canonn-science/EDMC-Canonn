---
name: spansh-system-lookup
description: Look up Elite Dangerous system coordinates and id64 from a system name using the Spansh API. Use this when writing code that needs to resolve a system name to its id64 or x/y/z coordinates via spansh.co.uk.
---

# Spansh System Lookup

This skill documents the established pattern used in this codebase to resolve an Elite Dangerous system name to its `id64` and galactic coordinates via the Spansh API.

---

## Step 1 — Resolve system name to id64 and coordinates

Use the `field_values/system_names` endpoint with the system name as query parameter `q`.
The response includes `id64` **and** galactic coordinates — no second API call needed for coords.

```python
import requests

def get_system_info(system_name):
    """Returns the matching entry from min_max, containing id64 and x/y/z coords."""
    headers = {"User-Agent": "Canonn <scriptname>.py"}
    url = f"https://spansh.co.uk/api/systems/field_values/system_names?q={system_name}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching system info for {system_name}: {r.status_code}")
        return None
    for system in (r.json().get("min_max") or []):
        if system.get("name") == system_name:
            return system
    return None
```

**Key details:**
- The response key is `"min_max"` (not `"results"` or `"systems"`).
- The endpoint returns fuzzy matches; always filter by exact name match (`system.get("name") == system_name`).
- Each entry in `min_max` contains `"name"`, `"id64"`, and `"x"`, `"y"`, `"z"` coordinates.

---

## Step 2 — Extract coordinates and id64 from the result

Coordinates are top-level keys in each `min_max` entry.

```python
info = get_system_info(system_name)
if info:
    id64 = info.get("id64")
    x    = info.get("x")
    y    = info.get("y")
    z    = info.get("z")
```

---

## Step 3 — Fetch full body data (only when needed)

Only call the dump endpoint if you need body-level details (bodies list, bodyCount, visit status, etc.).
It is slower — avoid it if coordinates and id64 are all you need.

```python
def get_system_dump(id64):
    headers = {"User-Agent": "Canonn <scriptname>.py"}
    url = f"https://spansh.co.uk/api/dump/{id64}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching system data for id64 {id64}: {r.status_code}")
        return None
    return r.json().get("system")
```

**Key details:**
- The response key is `"system"`.
- The returned object contains `"coords"` (nested), `"bodies"`, `"bodyCount"`, `"id64"`, `"name"`, etc.

---

## Combined helper (no caching)

```python
import requests

HEADERS = {"User-Agent": "Canonn <scriptname>.py"}

def get_system_coords_and_id64(system_name):
    """Returns (id64, x, y, z) for a system name using a single API call."""
    url = f"https://spansh.co.uk/api/systems/field_values/system_names?q={system_name}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None, "", "", ""
    for system in (r.json().get("min_max") or []):
        if system.get("name") == system_name:
            return system.get("id64"), system.get("x", ""), system.get("y", ""), system.get("z", "")
    return None, "", "", ""
```

---

## API Reference

| Endpoint | Purpose |
|---|---|
| `GET https://spansh.co.uk/api/systems/field_values/system_names?q={name}` | Resolve system name → id64 |
| `GET https://spansh.co.uk/api/dump/{id64}` | Full system data including coords and bodies |

### Response shapes

**`field_values/system_names`** — includes coordinates directly:
```json
{
  "min_max": [
    { "name": "Merope", "id64": 358665202332, "x": -78.59375, "y": -149.625, "z": -340.53125 }
  ]
}
```

**`dump/{id64}`** — only needed for body-level detail:
```json
{
  "system": {
    "id64": 358665202332,
    "name": "Merope",
    "coords": { "x": -78.59375, "y": -149.625, "z": -340.53125 },
    "bodyCount": 12,
    "bodies": [ ... ]
  }
}
```

---

## Notes

- Always set `User-Agent` header to identify the script (Spansh API etiquette).
- `min_max` returns fuzzy matches — always compare by exact name.
- The `coords` dict may be absent; use `system.get("coords") or {}` defensively.
- Use the `id64_cache.json` caching pattern for any script making repeated lookups across many systems.
