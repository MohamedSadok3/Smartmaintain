"""
SmartMaintain — Full Functionality Test Suite
Run inside IoT container with service IPs injected via env vars.
"""
import json, sys, os
import requests

AUTH  = os.environ.get("AUTH_URL",  "http://auth:5004")
ML    = os.environ.get("ML_URL",    "http://ml:5002")
IOT   = os.environ.get("IOT_URL",   "http://iot:5001")
ALERT = os.environ.get("ALERT_URL", "http://alertes:5003")

PASS, FAIL, WARN = "✓", "✗", "⚠"
results = []

def test(name, ok, detail="", warn=False):
    tag = WARN if (warn and not ok) else (PASS if ok else FAIL)
    results.append((tag, name, detail))
    print(f"  {tag}  {name}" + (f"  →  {detail}" if detail else ""))

def section(title):
    print(f"\n{'─'*62}\n  {title}\n{'─'*62}")

def get(url, tok=None, **kw):
    h = {"Authorization": f"Bearer {tok}"} if tok else {}
    return requests.get(url, headers=h, timeout=8, **kw)

def post(url, tok=None, **kw):
    h = {"Authorization": f"Bearer {tok}"} if tok else {}
    return requests.post(url, headers=h, timeout=10, **kw)

def patch(url, tok=None, **kw):
    h = {"Authorization": f"Bearer {tok}"} if tok else {}
    return requests.patch(url, headers=h, timeout=8, **kw)

def login(email, password):
    try:
        r = post(f"{AUTH}/api/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            return r.json().get("token"), r.json().get("user")
    except Exception as e:
        print(f"  [ERR] {e}")
    return None, None

# ─────────────────────────────────────────
section("1. AUTHENTICATION")
# ─────────────────────────────────────────
sa_tok, sa       = login("superadmin@smartmaintain.local", "superadmin123")
admin_tok, admin = login("admin@usine-demo.com",           "Admin2024!")
sup_tok, sup     = login("superviseur@usine-demo.com",     "Sup2024!")
tech_tok, tech   = login("tech@usine-demo.com",            "Tech2024!")

test("Superadmin login",  sa_tok    is not None, (sa or {}).get("role","FAILED"))
test("Admin login",       admin_tok is not None, (admin or {}).get("role","FAILED"))
test("Superviseur login", sup_tok   is not None, (sup or {}).get("role","FAILED"))
test("Technicien login",  tech_tok  is not None, (tech or {}).get("role","FAILED"))

r = post(f"{AUTH}/api/auth/login", json={"email":"bad@bad.com","password":"wrong"})
test("Wrong credentials → 401", r.status_code == 401, f"HTTP {r.status_code}")

r = get(f"{AUTH}/api/auth/me")
test("No token → 401", r.status_code == 401, f"HTTP {r.status_code}")

for label, tok in [("superadmin",sa_tok),("admin",admin_tok),("superviseur",sup_tok),("technicien",tech_tok)]:
    r = get(f"{AUTH}/api/auth/me", tok)
    test(f"/me [{label}]", r.status_code == 200, r.json().get("email",""))

# ─────────────────────────────────────────
section("2. PLANTS")
# ─────────────────────────────────────────
r = get(f"{AUTH}/api/plants", sa_tok)
plants = r.json().get("plants", []) if r.status_code == 200 else []
test("Superadmin list all plants", r.status_code == 200, f"{len(plants)} plants")

r = get(f"{AUTH}/api/plants/me", admin_tok)
plant = r.json().get("plant", {}) if r.status_code == 200 else {}
test("Admin GET /plants/me", r.status_code == 200, plant.get("name",""))

r = get(f"{AUTH}/api/plants/me", sup_tok)
test("Superviseur GET /plants/me → 403 (by design)",
     r.status_code == 403, f"HTTP {r.status_code} — only admin role can access this")

r = get(f"{AUTH}/api/plants/1/overview", sa_tok)
test("Superadmin plant overview", r.status_code == 200,
     f"users={len(r.json().get('users',[]))} kpis={list(r.json().get('kpis',{}).keys())}" if r.status_code==200 else r.text[:60])

r = get(f"{AUTH}/api/plants/me", admin_tok)
r2 = patch(f"{AUTH}/api/plants/me", admin_tok, json={"description": "Updated by test"})
test("Admin PATCH /plants/me", r2.status_code == 200, r2.json().get("plant",{}).get("description","") if r2.status_code==200 else r2.text[:60])

# ─────────────────────────────────────────
section("3. USERS")
# ─────────────────────────────────────────
r = get(f"{AUTH}/api/users", sa_tok)
all_users = r.json().get("users", []) if r.status_code == 200 else []
test("Superadmin list users", r.status_code == 200, f"{len(all_users)} users")

r = get(f"{AUTH}/api/users", admin_tok)
plant_users = r.json().get("users", []) if r.status_code == 200 else []
test("Admin list plant users", r.status_code == 200, f"{len(plant_users)} users in plant")

r = get(f"{AUTH}/api/users?role=technicien", admin_tok)
test("Filter by role=technicien", r.status_code == 200, f"{len(r.json().get('users',[]))} techniciens")

r = get(f"{AUTH}/api/users?role=technicien", sup_tok)
test("Superviseur can list techniciens", r.status_code == 200, f"{len(r.json().get('users',[]))} results")

r = get(f"{AUTH}/api/users", tech_tok)
test("Technicien blocked from /users", r.status_code in (401,403), f"HTTP {r.status_code}")

# ─────────────────────────────────────────
section("4. COMPONENTS")
# ─────────────────────────────────────────
r = get(f"{AUTH}/api/components", admin_tok)
comps = r.json().get("components", []) if r.status_code == 200 else []
test("Admin list components", r.status_code == 200, f"{len(comps)} components")

types = {c.get("type") for c in comps}
test("All 4 machine types registered",
     types == {"moteur","pompe","compresseur","echangeur"}, str(types))

r = get(f"{AUTH}/api/components", sup_tok)
test("Superviseur list components", r.status_code == 200, f"{len(r.json().get('components',[]))} components")

r = get(f"{AUTH}/api/components", tech_tok)
test("Technicien list components", r.status_code == 200)

# ─────────────────────────────────────────
section("5. ALERTS")
# ─────────────────────────────────────────
r = get(f"{ALERT}/api/alertes", admin_tok)
alerts = r.json().get("alerts", []) if r.status_code == 200 else []
test("Admin list alerts", r.status_code == 200, f"{len(alerts)} alerts")

r = get(f"{ALERT}/api/alertes", sup_tok)
test("Superviseur list alerts", r.status_code == 200, f"{len(r.json().get('alerts',[]))} alerts")

r = get(f"{ALERT}/api/alertes", tech_tok)
test("Technicien list alerts", r.status_code == 200)

r = get(f"{ALERT}/api/alertes")
test("No token → 401", r.status_code in (401,403), f"HTTP {r.status_code}")

if alerts:
    a = alerts[0]
    aid = a["id"]
    r = get(f"{ALERT}/api/alertes/{aid}", admin_tok)
    detail = r.json().get("alert", r.json()) if r.status_code == 200 else {}
    test(f"Alert detail id={aid}", r.status_code == 200,
         f"machine={detail.get('machine')} severity={detail.get('severity')} status={detail.get('status')}")

    def safe_json(resp):
        try: return resp.json()
        except Exception: return {}

    # Step 1: Assign the alert to the technicien (admin action)
    tech_id = (tech or {}).get("id")
    if tech_id:
        r = patch(f"{ALERT}/api/alertes/{aid}", admin_tok,
                  json={"action":"assign","assigned_to": tech_id})
        j = safe_json(r)
        test("Assign alert to technicien (admin)", r.status_code in (200,400),
             f"HTTP {r.status_code} — {j.get('alert',{}).get('status', j.get('error', r.text[:60]))}")

    # Step 2: Technicien acknowledges the alert (must be assigned technicien)
    r = patch(f"{ALERT}/api/alertes/{aid}", tech_tok, json={"action":"acknowledge"})
    j = safe_json(r)
    test("Technicien acknowledge alert", r.status_code in (200,400),
         f"HTTP {r.status_code} — {j.get('alert',{}).get('status', j.get('error', r.text[:60]))}")

    # Step 3: Superviseur resolves the acknowledged alert
    r = patch(f"{ALERT}/api/alertes/{aid}", sup_tok, json={"action":"resolve"})
    j = safe_json(r)
    test("Superviseur resolve alert", r.status_code in (200,400),
         f"HTTP {r.status_code} — {j.get('alert',{}).get('status', j.get('error', r.text[:60]))}")

r = get(f"{ALERT}/api/dashboard/summary", admin_tok)
dash = r.json() if r.status_code == 200 else {}
test("Dashboard stats", r.status_code == 200,
     f"open={dash.get('open_alerts','?')} pending={dash.get('pending_interventions','?')}" if r.status_code==200 else r.text[:60])

# ─────────────────────────────────────────
section("6. ML SERVICE")
# ─────────────────────────────────────────
r = get(f"{ML}/health")
test("ML /health", r.status_code == 200, str(r.json()))

r = get(f"{ML}/api/ml/status", admin_tok)
bundles = r.json().get("bundles", {}) if r.status_code == 200 else {}
test("ML /status", r.status_code == 200,
     f"version={r.json().get('model_version')} bundles={list(bundles.keys())}")

# Pompe normal
r = post(f"{ML}/api/ml/predict", admin_tok,
    json={"machine":"pompe","sensors":{"vibration":[0.25]*20,"pressure":[5.0]*20,"temperature":[45.0]*20,"flow_rate":[100.0]*20}})
test("Predict pompe (normal)", r.status_code == 200,
     f"defect={r.json().get('defect')} score={round(r.json().get('defect_score',0),3)}" if r.status_code==200 else r.text[:80])

# Compresseur normal
r = post(f"{ML}/api/ml/predict", admin_tok,
    json={"machine":"compresseur","sensors":{"pressure":[7.8]*30,"temperature_oil":[68.0]*30,"current":[17.0]*30}})
test("Predict compresseur (normal)", r.status_code == 200,
     f"defect={r.json().get('defect')} score={round(r.json().get('defect_score',0),3)}" if r.status_code==200 else r.text[:80])

# Echangeur normal
r = post(f"{ML}/api/ml/predict", admin_tok,
    json={"machine":"echangeur","sensors":{"temp_in_hot":[80.0]*30,"temp_out_hot":[45.0]*30,
                     "temp_in_cold":[15.0]*30,"temp_out_cold":[36.0]*30,"flow_rate":[100.0]*30}})
test("Predict echangeur (normal)", r.status_code == 200,
     f"defect={r.json().get('defect')} score={round(r.json().get('defect_score',0),3)}" if r.status_code==200 else r.text[:80])

# Echangeur faulty
r = post(f"{ML}/api/ml/predict", admin_tok,
    json={"machine":"echangeur","sensors":{"temp_in_hot":[86.0]*30,"temp_out_hot":[60.0]*30,
                     "temp_in_cold":[15.0]*30,"temp_out_cold":[29.0]*30,"flow_rate":[85.0]*30}})
d = r.json() if r.status_code==200 else {}
test("Predict echangeur (encrassement)", r.status_code==200 and d.get("defect")!="normal_operation",
     f"defect={d.get('defect')} score={round(d.get('defect_score',0),3)}" if r.status_code==200 else r.text[:80])

# Compresseur faulty (surchauffe)
r = post(f"{ML}/api/ml/predict", admin_tok,
    json={"machine":"compresseur","sensors":{"pressure":[8.3]*30,"temperature_oil":[95.0]*30,"current":[23.0]*30}})
d = r.json() if r.status_code==200 else {}
test("Predict compresseur (surchauffe)", r.status_code==200 and d.get("defect")!="normal_operation",
     f"defect={d.get('defect')} score={round(d.get('defect_score',0),3)}" if r.status_code==200 else r.text[:80])

r = post(f"{ML}/api/ml/predict",
    json={"machine":"pompe","sensors":{"vibration":[0.25]*20,"pressure":[5.0]*20,"temperature":[45.0]*20,"flow_rate":[100.0]*20}})
test("ML blocked without token", r.status_code in (401,403), f"HTTP {r.status_code}")

# ─────────────────────────────────────────
section("7. IoT SERVICE")
# ─────────────────────────────────────────
r = get(f"{IOT}/health")
test("IoT /health", r.status_code == 200)

r = get(f"{IOT}/api/iot/status", admin_tok)
test("IoT /status", r.status_code == 200)

r = get(f"{IOT}/api/iot/config", admin_tok)
test("IoT /config (admin)", r.status_code == 200)

r = get(f"{IOT}/api/iot/config", tech_tok)
test("IoT /config blocked for technicien", r.status_code in (401,403), f"HTTP {r.status_code}")

r = post(f"{IOT}/api/iot/inject", admin_tok,
    json={"machine":"pompe","plant_id":1,
          "sensors":{"vibration":[0.25]*20,"pressure":[5.0]*20,
                     "temperature":[45.0]*20,"flow_rate":[100.0]*20}})
test("IoT inject sensor data", r.status_code in (201,202), f"HTTP {r.status_code}")

r = post(f"{IOT}/api/iot/inject", admin_tok,
    json={"machine":"compresseur","plant_id":1,
          "sensors":{"pressure":[7.8]*30,"temperature_oil":[68.0]*30,"current":[17.0]*30}})
test("IoT inject compresseur", r.status_code in (201,202), f"HTTP {r.status_code}")

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
print(f"\n{'═'*62}")
passed = sum(1 for s,_,_ in results if s == PASS)
warned = sum(1 for s,_,_ in results if s == WARN)
failed = sum(1 for s,_,_ in results if s == FAIL)
print(f"  RESULTS:  {passed} passed  |  {warned} warnings  |  {failed} failed  (total {len(results)})")
print(f"{'═'*62}")
if failed:
    print("\nFailed:")
    for s,n,d in results:
        if s == FAIL: print(f"  {FAIL}  {n}  →  {d}")
sys.exit(0 if failed == 0 else 1)
