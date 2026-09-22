#!/bin/bash
cd /app
python3 << 'EOF'
import requests, json, time

BASE = "http://gateway:5000"
print("Connecting to gateway...")

try:
    r = requests.post(f"{BASE}/api/auth/login",
        json={"email": "admin@usine-demo.com", "password": "Admin2024!"})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login OK\n")
except Exception as e:
    print(f"❌ Login failed: {e}")
    exit(1)

print("=== PUMP LEAK INJECTIONS ===")
scenarios = [
    {"name": "LIGHT LEAK", "p": 4.2, "f": 75.0, "t": 48.0, "a1": 0.25, "a2": 0.28, "c": 10.5},
    {"name": "MODERATE LEAK", "p": 2.8, "f": 65.0, "t": 52.0, "a1": 0.35, "a2": 0.40, "c": 11.5},
    {"name": "CRITICAL LEAK", "p": 1.2, "f": 35.0, "t": 62.0, "a1": 0.65, "a2": 0.70, "c": 13.5},
]

for s in scenarios:
    body = {
        "machine": "pompe",
        "sensors": {
            "Accelerometer1RMS": [s["a1"]],
            "Accelerometer2RMS": [s["a2"]],
            "Current": [s["c"]],
            "Pressure": [s["p"]],
            "Temperature": [s["t"]],
            "Thermocouple": [s["t"] - 1],
            "Voltage": [220.0],
            "Volume Flow RateRMS": [s["f"]]
        }
    }
    try:
        r = requests.post(f"{BASE}/api/iot/inject", headers=h, json=body)
        score = r.json().get("anomaly_score", "?")
        print(f"  ✅ {s['name']:<20} | Score: {score}")
    except Exception as e:
        print(f"  ❌ {s['name']}: {e}")

print("\n⏳ Waiting 4s for processing...")
time.sleep(4)

print("\n=== ALERTS CREATED ===")
r = requests.get(f"{BASE}/api/alertes?machine=pompe&limit=10", headers=h)
alerts = r.json().get("alerts", [])
print(f"✅ Found {len(alerts)} alert(s):")
for a in alerts[:5]:
    print(f"  [{a['severity']:<8}] {a['machine']} - {a['alert_type']}")
    print(f"      Created: {a['created_at']}")

print("\n✅ Injection complete!")
EOF
