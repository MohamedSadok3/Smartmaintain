"""
SmartMaintain - Injection Test Script
Run: python inject_test.py
"""
import requests, json, time

BASE = "http://gateway:5000"

# Login
r = requests.post(f"{BASE}/api/auth/login",
    json={"email": "admin@usine-demo.com", "password": "Admin2024!"})
token = r.json()["token"]
h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(f"Login OK — role: {r.json()['user']['role']}\n")

injections = [
    {
        "label": "Compresseur (surchauffe)",
        "body": {
            "machine": "compresseur", "plant_id": 1,
            "sensors": {
                "pressure":         [8.3] * 30,
                "temperature_oil":  [95.0] * 30,
                "current":          [23.0] * 30
            }
        }
    },
    {
        "label": "Echangeur (encrassement)",
        "body": {
            "machine": "echangeur", "plant_id": 1,
            "sensors": {
                "temp_in_hot":   [86.0] * 30,
                "temp_out_hot":  [60.0] * 30,
                "temp_in_cold":  [15.0] * 30,
                "temp_out_cold": [29.0] * 30,
                "flow_rate":     [85.0] * 30
            }
        }
    },
    {
        "label": "Pompe (cavitation)",
        "body": {
            "machine": "pompe", "plant_id": 1,
            "sensors": {
                "vibration":   [2.8] * 20,
                "pressure":    [2.1] * 20,
                "temperature": [78.0] * 20,
                "flow_rate":   [42.0] * 20
            }
        }
    }
]

print("=== INJECTIONS ===")
for inj in injections:
    r = requests.post(f"{BASE}/api/iot/inject", headers=h, json=inj["body"])
    print(f"  [{r.status_code}] {inj['label']}")

print("\nWaiting 5s for ML pipeline...")
time.sleep(5)

# Check alerts
r = requests.get(f"{BASE}/api/alertes?limit=5", headers={"Authorization": f"Bearer {token}"})
alerts = r.json().get("alerts", [])
print(f"\n=== ALERTS CREATED (latest {len(alerts)}) ===")
for a in alerts:
    score = round(a["anomaly_score"] * 100, 1)
    print(f"  [{a['severity']:<8}] {a['machine']:<12} | {a['defect']:<22} | score={score}% | status={a['status']}")

# Dashboard
r = requests.get(f"{BASE}/api/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
d = r.json()
print(f"\n=== DASHBOARD ===")
print(f"  Open alerts        : {d.get('open_alerts')}")
print(f"  Pending interventions: {d.get('pending_interventions')}")
