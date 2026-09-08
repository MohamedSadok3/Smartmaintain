# 📋 WORKFLOW COMPLET - SmartMaintain Platform

## 🎯 Vue d'Ensemble

SmartMaintain est une plateforme IoT de maintenance prédictive industrielle basée sur une **architecture microservices** avec 9 services interconnectés.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                           │
│                      http://localhost:3000                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ WebSocket + HTTP
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    GATEWAY (API + WebSocket Hub)                    │
│                      http://localhost:5000                          │
│  • Authentification JWT                                             │
│  • Proxy des requêtes HTTP                                          │
│  • Bridge WebSocket (Redis → Frontend)                              │
└─────┬─────────┬──────────┬──────────┬──────────┬────────────────────┘
      │         │          │          │          │
      ↓         ↓          ↓          ↓          ↓
   ┌────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────────┐
   │AUTH│   │ IOT │   │ ML  │   │ALERT│   │POSTGRES │
   │    │   │     │   │     │   │     │   │  +DB    │
   └────┘   └─────┘   └─────┘   └─────┘   └─────────┘
               │         │         │
               └────┬────┴────┬────┘
                    ↓         ↓
               ┌────────┐ ┌──────────┐
               │ REDIS  │ │ MOSQUITTO│
               │Pub/Sub │ │   MQTT   │
               └────────┘ └──────────┘
```

---

## 🚀 1. DÉMARRAGE DE LA PLATEFORME

### 📌 Ordre de Démarrage (docker-compose)

```yaml
PHASE 1: Infrastructure Services
├─ 1. PostgreSQL      (base de données)
├─ 2. Redis           (pub/sub + cache)
└─ 3. Mosquitto       (broker MQTT)

PHASE 2: Database Migration
└─ 4. migrations      (one-shot: crée les tables + superadmin)

PHASE 3: Backend Services
├─ 5. auth            (dépend de: migrations)
├─ 6. iot             (dépend de: migrations, redis, mosquitto)
├─ 7. ml              (dépend de: redis)
└─ 8. alertes         (dépend de: migrations, redis)

PHASE 4: API Layer
└─ 9. gateway         (dépend de: auth, iot, ml, alertes)

PHASE 5: Frontend
└─ 10. frontend       (dépend de: gateway)
```

### 🔄 Health Checks

Chaque service attend que ses dépendances soient "healthy" :
- **PostgreSQL** : `pg_isready` (10 tentatives / 5s)
- **Redis** : `redis-cli ping` (10 tentatives / 5s)
- **Migrations** : `service_completed_successfully` (exit 0)

---

## 📊 2. WORKFLOW PAR SERVICE

### 🔐 **AUTH SERVICE** (Port interne: 8001)

**Rôle :** Gestion des utilisateurs, authentification, autorisation

**Endpoints :**
```
POST   /api/auth/login                    # JWT + refresh token
POST   /api/auth/register-plant           # Inscription usine
POST   /api/auth/logout

GET    /api/users                         # Liste utilisateurs
POST   /api/users                         # Créer utilisateur
PATCH  /api/users/:id                     # Modifier utilisateur
DELETE /api/users/:id                     # Supprimer utilisateur

GET    /api/plants                        # Liste usines
GET    /api/plants/:id                    # Détails usine
PATCH  /api/plants/:id                    # Modifier usine

GET    /api/components                    # Liste composants
POST   /api/components                    # Créer composant
PATCH  /api/components/:id                # Modifier composant
DELETE /api/components/:id                # Supprimer composant
```

**Tables PostgreSQL :**
- `users` : utilisateurs (superadmin, admin, operator)
- `plants` : usines industrielles
- `components` : équipements (pompe, moteur, compresseur, échangeur)

**Workflow typique :**
```
1. Frontend → POST /api/auth/login {email, password}
2. Auth vérifie dans PostgreSQL
3. Auth génère JWT (contient: user_id, role, plant_id)
4. Frontend stocke JWT dans localStorage
5. Toutes les requêtes suivantes incluent: Authorization: Bearer <JWT>
```

---

### 📡 **IOT SERVICE** (Port interne: 8002)

**Rôle :** Ingestion des données capteurs en temps réel

**Endpoints :**
```
GET    /api/iot/config                    # Config capteurs par composant
POST   /api/iot/config                    # Créer config capteur
PATCH  /api/iot/config/:id                # Modifier config
DELETE /api/iot/config/:id                # Supprimer config

GET    /api/iot/replay/status             # État replay CSV
POST   /api/iot/replay/start              # Démarrer simulation
POST   /api/iot/replay/stop               # Arrêter simulation
```

**Flux de données :**
```
1. ReplayService (thread background) lit les CSV :
   - backend/iot/data/pompe.csv
   - backend/iot/data/moteur.csv
   - backend/iot/data/compresseur.csv
   - backend/iot/data/echangeur.csv

2. Toutes les 2 secondes (IOT_REPLAY_INTERVAL_SECONDS) :
   - Lit une ligne du CSV
   - Publie sur Redis channel "sensor_data_raw"
   - Format : {component_id, machine, temperature, vibration, pressure, ...}

3. Optionnel : Publie aussi sur MQTT (non utilisé actuellement)
```

**Variables d'environnement :**
```env
IOT_PLANT_ID=1                          # ID usine
IOT_REPLAY_INTERVAL_SECONDS=2           # Fréquence envoi
IOT_NORMAL_BIAS=0.85                    # 85% données normales
```

---

### 🤖 **ML SERVICE** (Port interne: 8003)

**Rôle :** Prédictions de maintenance avec Machine Learning

**Endpoints :**
```
POST   /api/ml/predict                    # Prédiction manuelle
GET    /api/ml/status                     # État modèles
GET    /api/ml/status/manifest            # Versions modèles
GET    /api/ml/status/models/:machine     # Métadonnées modèle
```

**Workflow en temps réel :**
```
1. Thread Redis Consumer écoute "sensor_data_raw"

2. Pour chaque message reçu :
   ├─ Extrait les features (FeatureExtractorV7)
   ├─ Charge le modèle RandomForest correspondant
   │  - backend/ml/models_v7/pompe/model.pkl
   │  - backend/ml/models_v7/moteur/model.pkl
   │  - backend/ml/models_v7/compresseur/model.pkl
   │  - backend/ml/models_v7/echangeur/model.pkl
   │
   ├─ Fait la prédiction :
   │  - failure_risk (0-100%)
   │  - predicted_class (normal/warning/critical)
   │  - days_to_failure (estimation)
   │  - anomaly_score
   │
   └─ Publie sur Redis "ml_predictions" :
      {
        "component_id": 1,
        "machine": "pompe",
        "failure_risk": 75.2,
        "predicted_class": "warning",
        "days_to_failure": 15,
        "recommendation": "Inspecter roulements",
        "raw_data": {...},
        "timestamp": "2026-09-07T10:30:00Z"
      }
```

**Modèles ML :**
- **Algorithme :** Random Forest Classifier
- **Features :** 20+ (stats temperature, vibration, FFT, rolling windows)
- **Classes :** normal, warning, critical
- **Métriques :** 
  - Accuracy: ~95%
  - F1-score: ~0.93
  - Précision: ~0.96

---

### 🚨 **ALERTES SERVICE** (Port interne: 8004)

**Rôle :** Gestion des alertes et notifications temps réel

**Endpoints :**
```
GET    /api/alertes                       # Liste alertes (filtrées par plant)
GET    /api/alertes/:id                   # Détails alerte
PATCH  /api/alertes/:id                   # Modifier statut (acknowledged/resolved)
DELETE /api/alertes/:id                   # Supprimer alerte

GET    /api/dashboard/stats               # Statistiques dashboard
GET    /api/dashboard/recent              # Alertes récentes
```

**Workflow :**
```
1. Thread Redis Consumer écoute "ml_predictions"

2. Pour chaque prédiction reçue :
   ├─ Analyse le risque :
   │  - failure_risk > 70% → CRITICAL
   │  - failure_risk > 40% → WARNING
   │  - failure_risk ≤ 40% → NORMAL (pas d'alerte)
   │
   ├─ Si alerte détectée :
   │  ├─ Enregistre dans PostgreSQL (table alerts)
   │  └─ Émet WebSocket "alert:new" vers Gateway
   │
   └─ Émet toujours "sensor:data" vers Gateway (données temps réel)
```

**WebSocket Events émis :**
```javascript
// Nouvelle alerte
socket.emit('alert:new', {
  id: 123,
  component_id: 1,
  plant_id: 1,
  severity: 'critical',
  message: 'Risque élevé de panne',
  failure_risk: 85.3,
  recommendation: 'Maintenance urgente',
  status: 'pending'
});

// Données capteur temps réel
socket.emit('sensor:data', {
  component_id: 1,
  machine: 'pompe',
  failure_risk: 75.2,
  predicted_class: 'warning',
  temperature: 82.5,
  vibration: 45.2,
  timestamp: '2026-09-07T10:30:00Z'
});
```

**Table PostgreSQL :**
```sql
alerts:
  - id, component_id, plant_id
  - severity (warning/critical)
  - message, recommendation
  - failure_risk, predicted_class
  - status (pending/acknowledged/resolved)
  - created_at, resolved_at
```

---

### 🌐 **GATEWAY** (Port: 5000)

**Rôle :** API Gateway + WebSocket Hub + Authentification

**Fonctionnalités :**

#### 1️⃣ **Proxy HTTP**
```
Frontend Request → Gateway → Backend Service

Exemple :
GET http://localhost:5000/api/users
  ↓
  Gateway valide JWT
  ↓
  Gateway → http://auth:8001/api/users
  ↓
  Response retournée au frontend
```

**Services proxifiés :**
```
/api/auth/*       → AUTH_SERVICE   (auth:8001)
/api/users/*      → AUTH_SERVICE   (auth:8001)
/api/plants/*     → AUTH_SERVICE   (auth:8001)
/api/components/* → AUTH_SERVICE   (auth:8001)
/api/iot/*        → IOT_SERVICE    (iot:8002)
/api/ml/*         → ML_SERVICE     (ml:8003)
/api/alertes/*    → ALERTES_SERVICE (alertes:8004)
/api/dashboard/*  → ALERTES_SERVICE (alertes:8004)
```

#### 2️⃣ **Authentification JWT**
```python
@app.before_request
def require_jwt():
    # Routes publiques (pas de JWT requis)
    if request.path in ["/health", "/api/auth/login", "/api/auth/register-plant"]:
        return None
    
    # Validation JWT pour toutes les autres routes
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = decode_token(token)  # Vérifie signature + expiration
    
    # payload contient: {user_id, role, plant_id, exp}
```

#### 3️⃣ **WebSocket Bridge (PRINCIPAL)**
```
Redis "ml_predictions" → Gateway → Frontend WebSocket

MÉTHODE PRIMAIRE (redis_to_websocket_bridge) :
1. Écoute Redis channel "ml_predictions"
2. Reçoit les prédictions ML
3. Émet via Socket.IO vers le frontend :
   - Event: "sensor:data"
   - Isolation par plant_id (multi-tenant)

Rooms WebSocket :
- "plant:1" → utilisateurs de l'usine 1
- "plant:2" → utilisateurs de l'usine 2
- "role:superadmin" → tous les superadmins (voient tout)
```

#### 4️⃣ **Isolation Multi-Tenant**
```python
@socketio_server.on("connect")
def authenticate_socket(auth):
    token = auth.get("token")
    payload = decode_token(token)
    
    if payload["role"] == "superadmin":
        join_room("role:superadmin")  # Voit toutes les usines
    else:
        plant_id = payload["plant_id"]
        join_room(f"plant:{plant_id}")  # Voit uniquement son usine

def emit_to_tenant(event, data):
    plant_id = data["plant_id"]
    socketio_server.emit(event, data, to=f"plant:{plant_id}")
    socketio_server.emit(event, data, to="role:superadmin")
```

#### 5️⃣ **Connection Pooling**
```python
# Optimisation : pool HTTP persistent
http_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=20,  # 20 connexions simultanées
    pool_maxsize=20,
    max_retries=3
)
```

---

### 💻 **FRONTEND** (Port: 3000)

**Stack :** React 18 + Vite + TailwindCSS + Socket.IO Client

**Pages principales :**
```
/login                    → Authentification
/dashboard                → Vue d'ensemble (stats + graphes)
/surveillance             → Monitoring temps réel (WebSocket)
/alertes                  → Liste des alertes
/alertes/:id              → Détail alerte
/composants               → Gestion composants
/utilisateurs             → Gestion utilisateurs
/profile                  → Profil utilisateur

# SuperAdmin uniquement
/plants                   → Gestion usines
/registrations            → Approbation inscriptions
```

**WebSocket Client :**
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5000', {
  auth: {
    token: localStorage.getItem('token')
  },
  transports: ['websocket', 'polling']
});

// Écoute des données temps réel
socket.on('sensor:data', (data) => {
  console.log('Nouvelle donnée capteur:', data);
  // Met à jour le dashboard en temps réel
});

// Écoute des nouvelles alertes
socket.on('alert:new', (alert) => {
  console.log('Nouvelle alerte:', alert);
  // Notification visuelle + sonore
});
```

**Services API :**
```javascript
// authService.js
export const login = (email, password) => {
  return api.post('/api/auth/login', { email, password });
};

// dashboardService.js
export const getDashboardStats = () => {
  return api.get('/api/dashboard/stats');
};

// alerteService.js
export const getAlertes = (filters) => {
  return api.get('/api/alertes', { params: filters });
};
```

---

## 🔄 3. FLUX DE DONNÉES COMPLET (Exemple)

### 📊 Scénario : Une pompe commence à surchauffer

```
┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : INGESTION IoT                                             │
└─────────────────────────────────────────────────────────────────────┘

1. IOT Service (ReplayService thread) :
   - Lit backend/iot/data/pompe.csv
   - Ligne : timestamp,temp,vibration,pressure,rpm,current,flow
            2026-09-07 10:30:00,85.2,48.5,2.8,1450,12.5,450

2. Publie sur Redis "sensor_data_raw" :
   {
     "component_id": 1,
     "plant_id": 1,
     "machine": "pompe",
     "temperature": 85.2,
     "vibration": 48.5,
     "pressure": 2.8,
     "rpm": 1450,
     "current": 12.5,
     "flow": 450,
     "timestamp": "2026-09-07T10:30:00Z"
   }

┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : PRÉDICTION ML                                             │
└─────────────────────────────────────────────────────────────────────┘

3. ML Service (Redis Consumer thread) reçoit le message

4. Feature Extraction (FeatureExtractorV7) :
   - Stats de base : mean_temp, std_temp, max_temp
   - Rolling windows : temp_rolling_3, vibration_rolling_5
   - FFT : dominant_freq_temp, spectral_energy
   - Trends : temp_trend, vibration_rate
   → Total : 20 features

5. Prédiction (RandomForest) :
   - Model : backend/ml/models_v7/pompe/model.pkl
   - Input : [85.2, 48.5, 2.8, ...]
   - Output :
     * failure_risk = 78.5%
     * predicted_class = "warning"
     * days_to_failure = 12
     * anomaly_score = 0.82

6. Recommendation Engine :
   - Règle : temp > 80°C + vibration > 45 → "Vérifier roulements"

7. Publie sur Redis "ml_predictions" :
   {
     "component_id": 1,
     "plant_id": 1,
     "machine": "pompe",
     "failure_risk": 78.5,
     "predicted_class": "warning",
     "days_to_failure": 12,
     "anomaly_score": 0.82,
     "recommendation": "Vérifier les roulements",
     "raw_data": {
       "temperature": 85.2,
       "vibration": 48.5,
       ...
     },
     "timestamp": "2026-09-07T10:30:00Z",
     "model_version": "v7"
   }

┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : CRÉATION ALERTE                                           │
└─────────────────────────────────────────────────────────────────────┘

8. ALERTES Service (Redis Consumer thread) reçoit "ml_predictions"

9. Analyse du risque :
   - failure_risk = 78.5% > 70% → CRITICAL
   
10. Enregistre dans PostgreSQL :
    INSERT INTO alerts (
      component_id, plant_id, severity, message,
      failure_risk, predicted_class, recommendation,
      status, created_at
    ) VALUES (
      1, 1, 'critical', 'Risque critique de panne détecté',
      78.5, 'warning', 'Vérifier les roulements',
      'pending', NOW()
    );
    
11. Émet WebSocket "alert:new" (vers Gateway)

┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4 : BRIDGE GATEWAY                                            │
└─────────────────────────────────────────────────────────────────────┘

12. GATEWAY (redis_to_websocket_bridge) reçoit "ml_predictions"

13. Isolation multi-tenant :
    - plant_id = 1 → émet vers room "plant:1"
    - Émet aussi vers room "role:superadmin"

14. Émet WebSocket "sensor:data" aux clients connectés

┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5 : AFFICHAGE FRONTEND                                        │
└─────────────────────────────────────────────────────────────────────┘

15. FRONTEND (Socket.IO client) reçoit l'événement

16. Page Surveillance :
    - Met à jour le graph en temps réel
    - Affiche l'indicateur de risque (78.5%)
    - Classe "warning" → badge jaune

17. Notification :
    - Toast : "⚠️ Alerte critique sur Pompe #1"
    - Son : alertSound.mp3
    - Badge rouge sur l'icône d'alerte

18. Page Dashboard :
    - Incrémente compteur "Alertes critiques"
    - Ajoute dans "Alertes récentes"
    - Met à jour le graphique de tendance

┌─────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 6 : ACTION TECHNICIEN                                         │
└─────────────────────────────────────────────────────────────────────┘

19. Technicien clique sur l'alerte

20. Frontend → PATCH /api/alertes/123
    Body: { status: "acknowledged" }

21. Gateway → ALERTES Service

22. ALERTES met à jour PostgreSQL :
    UPDATE alerts
    SET status = 'acknowledged', acknowledged_at = NOW()
    WHERE id = 123;

23. Émet WebSocket "alert:updated"

24. Frontend reçoit la mise à jour
    - Badge passe de rouge à orange
    - Affiche "Pris en charge par Jean Dupont"
```

---

## 🔐 4. SÉCURITÉ & AUTORISATION

### JWT Token Structure
```json
{
  "user_id": 1,
  "email": "admin@smartmaintain.com",
  "role": "admin",
  "plant_id": 1,
  "exp": 1694097600,
  "iat": 1694011200
}
```

### Rôles & Permissions

| Rôle | Plant Access | Permissions |
|------|-------------|-------------|
| **superadmin** | Toutes | CRUD users, plants, components, alertes |
| **admin** | Une seule | CRUD components, users (même plant), read alertes |
| **operator** | Une seule | Read only (dashboard, alertes, composants) |

### Isolation des Données

```python
# Exemple : Liste des alertes
@alertes_bp.route("/", methods=["GET"])
@require_auth
def get_alertes():
    user = request.user  # Injecté par @require_auth
    
    if user["role"] == "superadmin":
        # Voit toutes les alertes
        alerts = Alert.query.all()
    else:
        # Voit uniquement son usine
        alerts = Alert.query.filter_by(plant_id=user["plant_id"]).all()
    
    return jsonify(alerts)
```

---

## 📈 5. MONITORING & OBSERVABILITÉ

### Health Checks

**Endpoint Gateway :** `GET /health`
```json
{
  "gateway": "ok",
  "auth": "ok",
  "iot": "ok",
  "ml": "ok",
  "alertes": "ok"
}
```

**Endpoints Individuels :**
- `GET http://auth:8001/health`
- `GET http://iot:8002/health`
- `GET http://ml:8003/health`
- `GET http://alertes:8004/health`

### Logs

Chaque service utilise le logging structuré :
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Voir les logs :**
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f ml

# 100 dernières lignes
docker-compose logs --tail=100 iot
```

### Métriques Clés

- **IOT** : Fréquence d'envoi (2s), Taux d'anomalies (15%)
- **ML** : Latence prédiction (<50ms), Accuracy (~95%)
- **Alertes** : Taux de création, Temps de résolution moyen
- **Gateway** : Requêtes/sec, Latence WebSocket

---

## 🔧 6. DÉVELOPPEMENT & DEBUGGING

### Développement Local

```bash
# Démarrer tous les services
docker-compose up -d

# Rebuild après modification code
docker-compose up -d --build ml

# Redémarrer un service
docker-compose restart iot

# Shell dans un conteneur
docker exec -it smartmaintain-ml-1 bash

# Arrêter tout
docker-compose down
```

### Variables d'Environnement (.env)

```env
# Database
POSTGRES_URL=postgresql://admin:secret@postgres:5432/smartmaintain
REDIS_URL=redis://redis:6379

# Auth
JWT_SECRET=change-me-in-production-use-a-long-random-secret
SUPERADMIN_EMAIL=sado9m3@gmail.com
SUPERADMIN_PASSWORD=superadmin123456

# ML
ML_MODEL_VERSION=v7
MOCK_ML=false

# IoT
IOT_REPLAY_INTERVAL_SECONDS=2
IOT_NORMAL_BIAS=0.85

# Email
MAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

### Debugging Common Issues

**Problème : Service ne démarre pas**
```bash
# Vérifier les logs
docker-compose logs service-name

# Vérifier l'état
docker ps -a

# Reconstruire
docker-compose build --no-cache service-name
```

**Problème : WebSocket ne se connecte pas**
```bash
# Vérifier Gateway logs
docker-compose logs -f gateway

# Tester manuellement
curl http://localhost:5000/health
```

**Problème : Prédictions ML ne s'affichent pas**
```bash
# Vérifier le flow Redis
docker exec -it smartmaintain-redis-1 redis-cli
> SUBSCRIBE ml_predictions
> SUBSCRIBE sensor_data_raw

# Vérifier ML logs
docker-compose logs -f ml
```

---

## 📚 7. RÉSUMÉ DES TECHNOLOGIES

| Service | Technologies | Base de données | Async |
|---------|-------------|-----------------|-------|
| **Auth** | Flask, SQLAlchemy | PostgreSQL | Non |
| **IoT** | Flask, Redis, MQTT | - | Thread (ReplayService) |
| **ML** | Flask, scikit-learn, pandas | - | Thread (Redis Consumer) |
| **Alertes** | Flask, SocketIO, Eventlet | PostgreSQL | Eventlet |
| **Gateway** | Flask, SocketIO, Eventlet | - | Eventlet + Threads |
| **Frontend** | React 18, Vite, Socket.IO | - | Non |

### Patterns Architecturaux

✅ **Microservices** : Services indépendants, déployables séparément  
✅ **Pub/Sub** : Communication asynchrone via Redis  
✅ **API Gateway** : Point d'entrée unique  
✅ **Multi-Tenancy** : Isolation par plant_id  
✅ **Event-Driven** : WebSocket pour temps réel  
✅ **CQRS** : Séparation read (GET) / write (POST/PATCH)  

---

## 🎓 CONCLUSION

Ce workflow montre comment **SmartMaintain** :
1. ✅ Ingère des données IoT en temps réel
2. ✅ Applique du Machine Learning pour prédire les pannes
3. ✅ Génère des alertes intelligentes
4. ✅ Notifie instantanément les techniciens via WebSocket
5. ✅ Isole les données par usine (multi-tenant)
6. ✅ Garantit la sécurité avec JWT

La plateforme est **production-ready** avec :
- 🔄 Auto-restart des services
- 💾 Persistance des données (PostgreSQL + volumes Docker)
- 🚀 Scalabilité horizontale (stateless services)
- 🔐 Sécurité (JWT + isolation multi-tenant)
- 📊 Observabilité (health checks + logs structurés)

---

**Dernière mise à jour :** 7 septembre 2026  
**Version :** 1.0  
**Auteur :** SmartMaintain Team
