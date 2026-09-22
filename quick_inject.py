#!/usr/bin/env python3
"""Quick injection test for pump leak alerts"""
import requests
import json
import time

BASE = "http://gateway:5000"
print("Connecting to gateway...")

# Login
try:
    r = requests.post(f"{BASE}/api/auth/login",
        json={"email": "admin@usine-demo.com", "password": "Admin2024!"})
    r.raise_for_status()
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"✅ Login OK\n")
except Exception as e:
    print(f"❌ Login failed: {e}")
    exit(1)

# Injection scenarios
print("=== PUMP LEAK INJECTIONS ===")
scenarios = [
    {"name": "LIGHT LEAK", "pressure": 4.2, "flow": 75.0, "temp": 48.0, "accel1": 0.25, "accel2": 0.28, "current": 10.5},
    {"name": "MODERATE LEAK", "pressure": 2.8, "flow": 65.0, "temp": 52.0, "accel1": 0.35, "accel2": 0.40, "current": 11.5},
    {"name": "CRITICAL LEAK", "pressure": 1.2, "flow": 35.0, "temp": 62.0, "accel1": 0.65, "accel2": 0.70, "current": 13.5},
]

for scenario in scenarios:
    body = {
        "machine": "pompe",
        "sensors": {
            "Accelerometer1RMS": [scenario["accel1"]],
            "Accelerometer2RMS": [scenario["accel2"]],
            "Current": [scenario["current"]],
            "Pressure": [scenario["pressure"]],
            "Temperature": [scenario["temp"]],
            "Thermocouple": [scenario["temp"] - 1],
            "Voltage": [220.0],
            "Volume Flow RateRMS": [scenario["flow"]]
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    try:
        r = requests.post(f"{BASE}/api/iot/inject", headers=h, json=body)
        r.raise_for_status()
        result = r.json()
        score = result.get("anomaly_score", "?")
        print(f"  ✅ {scenario['name']:<20} | Score: {score}")
    except Exception as e:
        print(f"  ❌ {scenario['name']}: {e}")

print("\n⏳ Waiting 4s for ML processing...")
time.sleep(4)

# Check alerts
print("\n=== ALERTS CREATED ===")
try:
    r = requests.get(f"{BASE}/api/alertes?machine=pompe&limit=10", 
                    headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    data = r.json()
    alerts = data.get("alerts", [])
    
    if alerts:
        print(f"✅ Found {len(alerts)} alert(s):\n")
        for a in alerts[:5]:
            print(f"  ⚠️  [{a['severity']:<8}] {a['machine']:<10} | {a['alert_type']:<20} | {a['created_at']}")
    else:
        print("ℹ️  No alerts found yet (may still be processing)")
except Exception as e:
    print(f"❌ Error fetching alerts: {e}")

print("\n✅ Injection test complete!")
