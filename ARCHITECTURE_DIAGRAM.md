# 🏗️ ARCHITECTURE DIAGRAMS - SmartMaintain

## 📊 1. VUE D'ENSEMBLE DU SYSTÈME

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    React SPA (Port 3000)                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐   │    │
│  │  │ Dashboard   │  │ Surveillance│  │ Alertes & Components │   │    │
│  │  │ Page        │  │ Temps Réel  │  │ Management           │   │    │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────────────────────────┘
                        │
                        │ HTTP + WebSocket
                        │
┌───────────────────────▼──────────────────────────────────────────────────┐
│                            API GATEWAY LAYER                             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               Gateway Service (Port 5000)                       │    │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐    │    │
│  │  │ HTTP Proxy   │  │ JWT Auth      │  │ WebSocket Hub    │    │    │
│  │  │              │  │ Middleware    │  │ (Multi-Tenant)   │    │    │
│  │  └──────────────┘  └───────────────┘  └──────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────┘    │
└────────┬──────────┬────────────┬────────────┬──────────────────────────┘
         │          │            │            │
         ▼          ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          MICROSERVICES LAYER                             │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐     │
│  │   AUTH   │  │   IoT    │  │    ML    │  │      ALERTES       │     │
│  │          │  │          │  │          │  │                    │     │
│  │ • Login  │  │ • CSV    │  │ • Random │  │ • Gestion alertes  │     │
│  │ • Users  │  │   Replay │  │   Forest │  │ • Dashboard stats  │     │
│  │ • Plants │  │ • MQTT   │  │ • Feature│  │ • WebSocket        │     │
│  │ • Compo. │  │ • Config │  │   Eng.   │  │   notifications    │     │
│  │          │  │          │  │ • Predict│  │                    │     │
│  │ Port     │  │ Port     │  │ Port     │  │ Port 8004          │     │
│  │ 8001     │  │ 8002     │  │ 8003     │  │                    │     │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └──────┬─────────────┘     │
│        │             │             │                │                   │
└────────┼─────────────┼─────────────┼────────────────┼───────────────────┘
         │             │             │                │
         ▼             ▼             ▼                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                              │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  PostgreSQL  │  │    Redis     │  │  Mosquitto   │                  │
│  │              │  │              │  │              │                  │
│  │ • users      │  │ • sensor_    │  │ • MQTT       │                  │
│  │ • plants     │  │   data_raw   │  │   Broker     │                  │
│  │ • components │  │ • ml_        │  │              │                  │
│  │ • alerts     │  │   predictions│  │ Port 1883    │                  │
│  │              │  │              │  │              │                  │
│  │ Port 5432    │  │ Port 6379    │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │                    MIGRATIONS (One-Shot)                    │         │
│  │  • 0001_initial_schema.sql                                 │         │
│  │  • 0002_seed_superadmin.sql                                │         │
│  │  • 0003_add_plant_id_to_alerts.sql                         │         │
│  │  • 0004_consolidate_iot_config_tables.sql                  │         │
│  └────────────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 2. FLUX DE DONNÉES EN TEMPS RÉEL

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME DATA FLOW PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────┘

ÉTAPE 1: INGESTION IoT
──────────────────────
┌──────────────┐
│  CSV Files   │  pompe.csv, moteur.csv, compresseur.csv, echangeur.csv
│  (Historical │
│     Data)    │
└──────┬───────┘
       │ Read (every 2s)
       │
       ▼
┌──────────────────────┐
│   IoT Service        │
│   ReplayService      │  Thread background
│   (Thread)           │
└──────────┬───────────┘
           │
           │ PUBLISH
           ▼
┌─────────────────────────────────────┐
│   Redis Channel: "sensor_data_raw"  │
│                                     │
│   {                                 │
│     component_id: 1,                │
│     machine: "pompe",               │
│     temperature: 78.5,              │
│     vibration: 42.3,                │
│     pressure: 2.5,                  │
│     ...                             │
│   }                                 │
└──────────────┬──────────────────────┘
               │
               │ SUBSCRIBE
               │
               ▼
ÉTAPE 2: MACHINE LEARNING
──────────────────────────
┌──────────────────────┐
│   ML Service         │
│   Redis Consumer     │  Thread background
│   (Thread)           │
└──────────┬───────────┘
           │
           │ 1. Extract Features (20+)
           │ 2. Load RandomForest Model
           │ 3. Predict Risk
           │
           ▼
┌─────────────────────────────────────┐
│  Prediction Result                  │
│                                     │
│  {                                  │
│    failure_risk: 78.5%,             │
│    predicted_class: "warning",      │
│    days_to_failure: 15,             │
│    anomaly_score: 0.82,             │
│    recommendation: "Check bearings" │
│  }                                  │
└──────────────┬──────────────────────┘
               │
               │ PUBLISH
               ▼
┌─────────────────────────────────────┐
│  Redis Channel: "ml_predictions"    │
└──────────────┬──────────────────────┘
               │
               │ SUBSCRIBE (2 consumers)
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
ÉTAPE 3A: ALERTES    ÉTAPE 3B: GATEWAY
──────────────────   ───────────────────
┌──────────────┐     ┌─────────────────┐
│   Alertes    │     │    Gateway      │
│   Service    │     │    Redis        │
│              │     │    Consumer     │
└──────┬───────┘     └────────┬────────┘
       │                      │
       │ IF risk > 70%        │
       │                      │
       ▼                      │
┌──────────────┐              │
│  PostgreSQL  │              │
│  INSERT      │              │
│  alert       │              │
└──────┬───────┘              │
       │                      │
       │ Emit WebSocket       │ Emit WebSocket
       │ "alert:new"          │ "sensor:data"
       │                      │
       └──────────┬───────────┘
                  │
                  ▼
ÉTAPE 4: GATEWAY BROADCAST
────────────────────────────
┌─────────────────────────────┐
│      Gateway WebSocket      │
│      Multi-Tenant Rooms     │
│                             │
│  • room: "plant:1"          │
│  • room: "plant:2"          │
│  • room: "role:superadmin"  │
└─────────────┬───────────────┘
              │
              │ Socket.IO emit
              │
              ▼
ÉTAPE 5: FRONTEND
──────────────────
┌───────────────────────────────┐
│    React App (Socket.IO)      │
│                               │
│  socket.on('sensor:data')     │
│  socket.on('alert:new')       │
│                               │
│  → Update Dashboard           │
│  → Show Notification          │
│  → Play Alert Sound           │
│  → Update Real-time Graph     │
└───────────────────────────────┘
```

---

## 🔐 3. AUTHENTIFICATION & AUTORISATION

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      JWT AUTHENTICATION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

1. LOGIN
────────
   Frontend                Gateway               Auth Service
      │                       │                       │
      │  POST /api/auth/login │                       │
      ├──────────────────────►│                       │
      │  {email, password}    │                       │
      │                       │  Forward              │
      │                       ├──────────────────────►│
      │                       │                       │
      │                       │                  ┌────┴────┐
      │                       │                  │ Verify  │
      │                       │                  │ in      │
      │                       │                  │ Postgres│
      │                       │                  └────┬────┘
      │                       │                       │
      │                       │  JWT Token + User     │
      │                       │◄──────────────────────┤
      │  200 OK               │                       │
      │◄──────────────────────┤                       │
      │  {                    │                       │
      │    token: "eyJhbG...",│                       │
      │    user: {...}        │                       │
      │  }                    │                       │
      │                       │                       │
   Store in                   │                       │
   localStorage               │                       │


2. REQUÊTES AUTHENTIFIÉES
───────────────────────────
   Frontend                Gateway               Backend Service
      │                       │                       │
      │  GET /api/alertes     │                       │
      │  Authorization:       │                       │
      │  Bearer <JWT>         │                       │
      ├──────────────────────►│                       │
      │                       │                       │
      │                  ┌────┴────┐                  │
      │                  │ Decode  │                  │
      │                  │ JWT     │                  │
      │                  │ Verify  │                  │
      │                  │ Signature│                 │
      │                  └────┬────┘                  │
      │                       │                       │
      │                       │  IF valid → Forward   │
      │                       ├──────────────────────►│
      │                       │                       │
      │                       │                  ┌────┴─────┐
      │                       │                  │ Filter   │
      │                       │                  │ by       │
      │                       │                  │ plant_id │
      │                       │                  └────┬─────┘
      │                       │                       │
      │                       │  Response             │
      │                       │◄──────────────────────┤
      │  200 OK               │                       │
      │◄──────────────────────┤                       │
      │  [alerts]             │                       │


3. WEBSOCKET AUTHENTICATION
─────────────────────────────
   Frontend                Gateway
      │                       │
      │  socket.connect({     │
      │    auth: {            │
      │      token: JWT       │
      │    }                  │
      │  })                   │
      ├──────────────────────►│
      │                       │
      │                  ┌────┴────┐
      │                  │ Decode  │
      │                  │ JWT     │
      │                  │         │
      │                  │ Extract │
      │                  │ plant_id│
      │                  │         │
      │                  │ Join    │
      │                  │ Room    │
      │                  └────┬────┘
      │                       │
      │  Connection OK        │
      │◄──────────────────────┤
      │  (Joined "plant:1")   │
```

---

## 🏢 4. MULTI-TENANCY (ISOLATION PAR USINE)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MULTI-TENANT ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

DATABASE LEVEL (PostgreSQL)
────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│                         plants                              │
├────────┬─────────────────┬──────────────┬──────────────────┤
│ id     │ name            │ status       │ created_at       │
├────────┼─────────────────┼──────────────┼──────────────────┤
│ 1      │ Usine Paris     │ approved     │ 2024-01-01       │
│ 2      │ Usine Lyon      │ approved     │ 2024-01-15       │
│ 3      │ Usine Marseille │ pending      │ 2024-02-01       │
└────────┴─────────────────┴──────────────┴──────────────────┘
               │
               │ FK: plant_id
               │
       ┌───────┴────────┬──────────────┐
       │                │              │
       ▼                ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   users     │  │ components  │  │   alerts    │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ plant_id: 1 │  │ plant_id: 1 │  │ plant_id: 1 │
│ plant_id: 2 │  │ plant_id: 2 │  │ plant_id: 2 │
└─────────────┘  └─────────────┘  └─────────────┘


APPLICATION LEVEL (Query Filtering)
─────────────────────────────────────
def get_alerts():
    user = decode_token(request.headers['Authorization'])
    
    if user['role'] == 'superadmin':
        # Accès à TOUTES les usines
        alerts = Alert.query.all()
    else:
        # Accès uniquement à SON usine
        alerts = Alert.query.filter_by(
            plant_id=user['plant_id']
        ).all()
    
    return jsonify(alerts)


WEBSOCKET LEVEL (Room Isolation)
──────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│                    Gateway WebSocket                        │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐│
│  │  Room: plant:1  │  │  Room: plant:2  │  │ Room: SA    ││
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤│
│  │ User A (Admin)  │  │ User B (Admin)  │  │ SuperAdmin  ││
│  │ User C (Op.)    │  │ User D (Op.)    │  │ (sees all)  ││
│  └─────────────────┘  └─────────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────┘
         │                     │                     │
         │ Only receives       │ Only receives       │ Receives
         │ plant:1 events      │ plant:2 events      │ ALL events
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Usine Paris     │  │ Usine Lyon      │  │ All Plants      │
│ Dashboard       │  │ Dashboard       │  │ Admin Panel     │
└─────────────────┘  └─────────────────┘  └─────────────────┘


EMIT STRATEGY
─────────────
def emit_to_tenant(event, data):
    plant_id = data['plant_id']
    
    # Émet aux utilisateurs de l'usine
    socketio.emit(event, data, to=f"plant:{plant_id}")
    
    # Émet AUSSI aux superadmins
    socketio.emit(event, data, to="role:superadmin")
```

---

## 🔄 5. REDIS PUB/SUB ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        REDIS MESSAGE BUS                                │
└─────────────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │    REDIS     │
                         │  (Port 6379) │
                         └──────┬───────┘
                                │
                ┌───────────────┼────────────────┐
                │               │                │
         CHANNEL 1       CHANNEL 2        CHANNEL 3
         (sensor_data_raw)(ml_predictions) (alerts)
                │               │                │
                │               │                │
    ┌───────────┴─────┐  ┌──────┴──────────┐    │
    │                 │  │                 │    │
    ▼                 │  ▼                 │    ▼
PUBLISHER:        SUBSCRIBER:    PUBLISHER:    SUBSCRIBERS:
IoT Service       ML Service      ML Service   - Alertes Service
                                               - Gateway Service


CHANNEL 1: sensor_data_raw
───────────────────────────
Publisher: IoT Service
Subscribers: ML Service

Message Format:
{
  "component_id": 1,
  "plant_id": 1,
  "machine": "pompe",
  "temperature": 78.5,
  "vibration": 42.3,
  "pressure": 2.5,
  "rpm": 1450,
  "current": 12.5,
  "flow": 450,
  "timestamp": "2026-09-07T10:30:00Z"
}

Frequency: Every 2 seconds (configurable)


CHANNEL 2: ml_predictions
──────────────────────────
Publisher: ML Service
Subscribers: Alertes Service, Gateway Service

Message Format:
{
  "component_id": 1,
  "plant_id": 1,
  "machine": "pompe",
  "failure_risk": 78.5,
  "predicted_class": "warning",
  "days_to_failure": 15,
  "anomaly_score": 0.82,
  "recommendation": "Vérifier les roulements",
  "raw_data": {...},
  "timestamp": "2026-09-07T10:30:00Z",
  "model_version": "v7"
}

Frequency: Every 2 seconds (same as sensor data)


CHANNEL 3: alerts (unused currently)
─────────────────────────────────────
Reserved for future alert broadcasting
```

---

## 📦 6. DOCKER COMPOSE DEPENDENCY GRAPH

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE DEPENDENCIES                          │
└─────────────────────────────────────────────────────────────────────────┘

LEVEL 0: Infrastructure
───────────────────────
┌──────────┐  ┌──────────┐  ┌──────────┐
│ postgres │  │  redis   │  │mosquitto │
│ (healthy)│  │ (healthy)│  │ (started)│
└─────┬────┘  └─────┬────┘  └─────┬────┘
      │             │             │
      └─────────────┴─────────────┘
                    │
                    ▼
LEVEL 1: Database Setup
────────────────────────
            ┌──────────────┐
            │  migrations  │
            │ (completed)  │
            └──────┬───────┘
                   │
        ┌──────────┼─────────────────┐
        │          │                 │
        ▼          ▼                 ▼
LEVEL 2: Backend Services
──────────────────────────
  ┌──────┐   ┌──────┐   ┌──────────┐
  │ auth │   │ iot  │   │ alertes  │
  │      │   │      │   │          │
  └───┬──┘   └──┬───┘   └────┬─────┘
      │         │            │
      └─────────┴────────────┘
                │
                │     ┌──────┐
                │     │  ml  │
                │     │      │
                │     └───┬──┘
                │         │
        ┌───────┴─────────┴─────┐
        │                       │
        ▼                       ▼
LEVEL 3: Gateway
─────────────────
            ┌──────────┐
            │ gateway  │
            │ (started)│
            └─────┬────┘
                  │
                  ▼
LEVEL 4: Frontend
──────────────────
            ┌──────────┐
            │ frontend │
            │          │
            └──────────┘


DEPENDENCY RULES
─────────────────
auth      depends_on: migrations (completed)
iot       depends_on: migrations (completed), redis (healthy), mosquitto (started)
ml        depends_on: redis (healthy)
alertes   depends_on: migrations (completed), redis (healthy)
gateway   depends_on: auth, iot, ml, alertes (all started)
frontend  depends_on: gateway (started)
```

---

## 🎯 7. CYCLE DE VIE D'UNE ALERTE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ALERT LIFECYCLE STATE MACHINE                      │
└─────────────────────────────────────────────────────────────────────────┘

                        ┌────────────────┐
                        │  SENSOR DATA   │
                        │  (Normal ops)  │
                        └────────┬───────┘
                                 │
                                 │ failure_risk > 70%
                                 ▼
                        ┌────────────────┐
                        │    PENDING     │◄────────┐
                        │                │         │
                        │ Status: pending│         │
                        │ Color: Red     │         │ Reset if
                        │ Action: NONE   │         │ resolved
                        └────────┬───────┘         │ incorrectly
                                 │                 │
                                 │ Technicien      │
                                 │ acknowledges    │
                                 ▼                 │
                        ┌────────────────┐         │
                        │  ACKNOWLEDGED  │         │
                        │                │         │
                        │ Status: ack.   │         │
                        │ Color: Orange  │         │
                        │ Action: In work│         │
                        └────────┬───────┘         │
                                 │                 │
                                 │ Maintenance     │
                                 │ completed       │
                                 ▼                 │
                        ┌────────────────┐         │
                        │    RESOLVED    │─────────┘
                        │                │
                        │ Status: resolved
                        │ Color: Green   │
                        │ Action: Closed │
                        └────────┬───────┘
                                 │
                                 │ Archived after 30 days
                                 ▼
                        ┌────────────────┐
                        │    ARCHIVED    │
                        │  (soft delete) │
                        └────────────────┘


API ACTIONS
───────────
POST   /api/alertes           → Impossible (auto-créées par ML)
GET    /api/alertes           → Liste filtré par plant_id
GET    /api/alertes/:id       → Détails
PATCH  /api/alertes/:id       → Changer status (pending → acknowledged → resolved)
DELETE /api/alertes/:id       → Archiver (superadmin only)


NOTIFICATIONS
─────────────
State Change            → WebSocket Event → Frontend Action
─────────────────────────────────────────────────────────────────
pending                 → alert:new       → Sound + Toast + Badge
acknowledged            → alert:updated   → Update UI + Badge color
resolved                → alert:updated   → Remove from active list
```

---

## 🔍 8. MODÈLE DE DONNÉES COMPLET

```sql
-- USERS & AUTHENTICATION
─────────────────────────
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) CHECK (role IN ('superadmin', 'admin', 'operator')),
    plant_id INTEGER REFERENCES plants(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- PLANTS (USINES)
──────────────────
CREATE TABLE plants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    admin_email VARCHAR(255),
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by INTEGER REFERENCES users(id)
);

-- COMPONENTS (ÉQUIPEMENTS)
───────────────────────────
CREATE TABLE components (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    name VARCHAR(255) NOT NULL,
    machine_type VARCHAR(50) CHECK (machine_type IN ('pompe', 'moteur', 'compresseur', 'echangeur')),
    location VARCHAR(255),
    installation_date DATE,
    last_maintenance DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- IOT CONFIGURATION
────────────────────
CREATE TABLE iot_config (
    id SERIAL PRIMARY KEY,
    component_id INTEGER NOT NULL REFERENCES components(id),
    sensor_type VARCHAR(50),
    threshold_value FLOAT,
    unit VARCHAR(20),
    config_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ALERTS
─────────
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    component_id INTEGER NOT NULL REFERENCES components(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    severity VARCHAR(20) CHECK (severity IN ('warning', 'critical')),
    message TEXT NOT NULL,
    failure_risk FLOAT,
    predicted_class VARCHAR(20),
    days_to_failure INTEGER,
    recommendation TEXT,
    status VARCHAR(20) CHECK (status IN ('pending', 'acknowledged', 'resolved')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    acknowledged_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id),
    metadata JSONB
);

-- SCHEMA MIGRATIONS
────────────────────
CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW()
);


RELATIONS
─────────
users ────┐
          │ (plant_id)
          ▼
        plants ────┐
                   │ (plant_id)
                   ▼
              components ────┐
                             │ (component_id)
                   ┌─────────┴─────────┐
                   │                   │
                   ▼                   ▼
              iot_config            alerts


INDEXES (Performance)
──────────────────────
CREATE INDEX idx_users_plant_id ON users(plant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_components_plant_id ON components(plant_id);
CREATE INDEX idx_alerts_component_id ON alerts(component_id);
CREATE INDEX idx_alerts_plant_id ON alerts(plant_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
```

---

**Document créé le :** 7 septembre 2026  
**Version :** 1.0  
**Auteur :** SmartMaintain Team
