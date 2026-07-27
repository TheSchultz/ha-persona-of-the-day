"""End-to-end test against a throwaway Home Assistant instance.

Usage:
    docker run -d --name ha-persona-test -p 8124:8123 \
      -v $PWD/testconfig:/config homeassistant/home-assistant:stable
    # (copy custom_components/ into testconfig/ first)
    python3 scripts/e2e_test.py

Drives a FRESH instance (onboarding included) through the full user
journey: config flow, first-boot seeding, re-roll button, import
validation, options-flow paste, catalog reset, entry reload.
"""
import json
import sys
import time
import urllib.request

BASE = "http://localhost:8124"
CLIENT = f"{BASE}/"
results = []


def req(path, data=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body = e.read() or b""
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, body.decode(errors="replace")


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail else ""))


# --- Onboarding ---
status, out = req("/api/onboarding/users", {
    "client_id": CLIENT, "name": "Test User", "username": "tester",
    "password": "persona-test-pw-1", "language": "en",
})
auth_code = out["auth_code"]

# Exchange code for token (form-encoded endpoint)
form = f"grant_type=authorization_code&code={auth_code}&client_id={CLIENT}"
r = urllib.request.Request(BASE + "/auth/token", data=form.encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(r, timeout=30) as resp:
    TOKEN = json.load(resp)["access_token"]

req("/api/onboarding/core_config", {}, TOKEN)
req("/api/onboarding/analytics", {}, TOKEN)
req("/api/onboarding/integration", {"client_id": CLIENT, "redirect_uri": CLIENT}, TOKEN)
print("onboarding complete")

# --- 1. Config flow (as the UI does it) ---
status, flow = req("/api/config/config_entries/flow",
                   {"handler": "persona_rotator", "show_advanced_options": False}, TOKEN)
check("config flow starts", status == 200 and flow.get("step_id") == "user",
      f"status={status} step={flow.get('step_id') if isinstance(flow, dict) else flow}")
status, done = req(f"/api/config/config_entries/flow/{flow['flow_id']}", {}, TOKEN)
check("config flow creates entry", done.get("type") == "create_entry",
      f"type={done.get('type')}")
entry_id = done["result"]["entry_id"]

time.sleep(3)

# --- 2. Sensor exists with a persona from the catalog ---
status, sensor = req("/api/states/sensor.persona_of_the_day", token=TOKEN)
attrs = sensor.get("attributes", {}) if status == 200 else {}
check("sensor.persona_of_the_day exists", status == 200, f"status={status}")
check("persona picked on first boot", bool(sensor.get("state")) and sensor["state"] != "like a friendly assistant",
      f"state={sensor.get('state')!r}")
check("catalog seeded with 121", attrs.get("catalog_size") == 121,
      f"catalog_size={attrs.get('catalog_size')}")
check("history started", attrs.get("history_count") == 1,
      f"history_count={attrs.get('history_count')}")
first_persona = sensor.get("state")

# --- 3. Re-roll button ---
status, _ = req("/api/services/button/press",
                {"entity_id": "button.persona_re_roll"}, TOKEN)
time.sleep(1)
_, sensor2 = req("/api/states/sensor.persona_of_the_day", token=TOKEN)
check("button re-roll works", status == 200 and sensor2["state"] != first_persona,
      f"{first_persona!r} -> {sensor2['state']!r}")
check("history grows on re-roll", sensor2["attributes"]["history_count"] == 2)

# --- 4. import_personas service: valid + rejected lines ---
paste = """like a test robot butler with squeaky joints
- like a quoted list item persona
2. like a numbered persona from a chatbot
[has brackets so must be rejected]
""" + "x" * 150
status, _ = req("/api/services/persona_rotator/import_personas",
                {"personas": paste}, TOKEN)
time.sleep(1)
_, sensor3 = req("/api/states/sensor.persona_of_the_day", token=TOKEN)
cat = sensor3["attributes"]["catalog"]
check("import: valid lines added", sensor3["attributes"]["catalog_size"] == 124,
      f"catalog_size={sensor3['attributes']['catalog_size']} (expected 124)")
check("import: list markers stripped", "like a quoted list item persona" in cat)
check("import: numbering stripped", "like a numbered persona from a chatbot" in cat)
check("import: brackets rejected", not any("[" in p for p in cat))
check("import: overlong rejected", not any(len(p) > 120 for p in cat))

# --- 5. all-invalid import raises a service error ---
status, err = req("/api/services/persona_rotator/import_personas",
                  {"personas": "[only][brackets][here]"}, TOKEN)
check("all-invalid import returns error", status in (400, 500),
      f"status={status}")

# --- 6. options flow paste box ---
status, oflow = req(f"/api/config/config_entries/options/flow",
                    {"handler": entry_id, "show_advanced_options": False}, TOKEN)
check("options flow opens", status == 200 and oflow.get("step_id") == "init",
      f"status={status}")
status, odone = req(f"/api/config/config_entries/options/flow/{oflow['flow_id']}",
                    {"personas": "like an options flow test persona"}, TOKEN)
check("options flow submits", odone.get("type") == "create_entry", f"type={odone.get('type')}")
time.sleep(2)
_, sensor4 = req("/api/states/sensor.persona_of_the_day", token=TOKEN)
check("options paste imported", "like an options flow test persona" in sensor4["attributes"]["catalog"])
status, entry = req(f"/api/config/config_entries/entry/{entry_id}", token=TOKEN)

# --- 7. reset catalog ---
req("/api/services/persona_rotator/reset_catalog", {}, TOKEN)
time.sleep(1)
_, sensor5 = req("/api/states/sensor.persona_of_the_day", token=TOKEN)
check("reset restores built-in 121", sensor5["attributes"]["catalog_size"] == 121)

# --- 8. reload survives, state persists ---
status, _ = req(f"/api/config/config_entries/entry/{entry_id}/reload", {}, TOKEN)
time.sleep(3)
_, sensor6 = req("/api/states/sensor.persona_of_the_day", token=TOKEN)
check("entry reloads cleanly", status == 200 and bool(sensor6.get("state")))
check("persona persists across reload", sensor6["state"] == sensor2["state"],
      f"{sensor2['state']!r} vs {sensor6['state']!r}")

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
