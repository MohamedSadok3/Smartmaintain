# SmartMaintain Application

**Plateforme de maintenance prédictive temps réel**

---

## 🚀 Démarrage Rapide

### Prérequis

- Docker Desktop 20.10+
- 8 GB RAM minimum
- Windows 10/11

### Installation (3 commandes)

```powershell
# 1. Copier configuration
Copy-Item .env.example .env

# 2. Lancer services
docker-compose up -d

# 3. Ouvrir application
Start-Process "http://localhost:3000"
```

**Compte initial**: défini par `SUPERADMIN_EMAIL` et `SUPERADMIN_PASSWORD` dans `.env`.

---

## 📦 Services Disponibles

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interface React |
| **API Gateway** | http://localhost:5000 | API principale |
| **Auth Service** | réseau Docker uniquement | Authentification |
| **Alertes** | réseau Docker uniquement | Gestion alertes |
| **ML Service** | réseau Docker uniquement | Prédictions ML |
| **IoT Service** | réseau Docker uniquement | Ingestion données |
| **PostgreSQL** | réseau Docker uniquement | Base de données |
| **Redis** | réseau Docker uniquement | Pub/Sub + Cache |

---

## ⚙️ Configuration

### Fichier `.env`

```bash
# Base de données
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=smartmaintain

# JWT
JWT_SECRET_KEY=your-secret-key-here  # ⚠️ Changer!

# ML Mode
# Les quatre modèles sont chargés automatiquement.

# Email (optionnel)
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Générer Clé JWT Sécurisée

```powershell
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

---

## 🐳 Commandes Docker

### Gestion Services

```bash
# Démarrer tout
docker-compose up -d

# Arrêter tout
docker-compose down

# Voir logs
docker-compose logs -f [service]

# Redémarrer un service
docker-compose restart [service]

# Status
docker-compose ps
```

### Rebuild Après Modifications

```bash
# Rebuild service ML
docker-compose build ml
docker-compose up -d ml

# Rebuild tout
docker-compose build
docker-compose up -d
```

### Maintenance

```bash
# Nettoyer containers arrêtés
docker system prune

# Backup base de données
docker-compose exec -T postgres pg_dump -U postgres smartmaintain > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres smartmaintain < backup.sql
```

---

## 🔍 Vérification Installation

### Health Checks

```bash
# Vérifier tous les services
curl http://localhost:5000/health  # Gateway
docker compose exec auth python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5004/health').read())"
docker compose exec alertes python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5003/health').read())"
docker compose exec iot python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5001/health').read())"
```

**Attendu**: Tous retournent `{"status": "ok"}`

### Vérifier Modèles ML

```bash
docker-compose exec ml python -c "
from services.ml_service import MLService
svc = MLService()
status = svc.get_status()
print('Model version:', status.get('model_version'))
print('Models loaded:', list(svc.engine.models.keys()))
"
```

**Attendu**:
```
Model version: latest
Models loaded: ['moteur', 'pompe', 'compresseur', 'echangeur']
```

### Vérifier Flux Données

```bash
# Voir logs IoT
docker-compose logs -f iot | Select-String "Publishing"

# Voir prédictions ML
docker-compose logs -f ml | Select-String "Prediction"

# Écouter Redis
docker-compose exec redis redis-cli --csv PSUBSCRIBE '*'
```

---

## 🎨 Structure Application

```
smartmaintain/
├── backend/
│   ├── gateway/         # API Gateway + WebSocket
│   ├── auth/            # JWT Auth + Users
│   ├── ml/              # XGBoost Models
│   ├── iot/             # CSV Replay + Features
│   ├── alertes/         # Alertes System
│   ├── migrations/      # Schéma PostgreSQL versionné
│   └── shared/          # Constantes partagées
│
├── frontend/
│   └── src/
│       ├── pages/       # LoginPage, DashboardPage, etc.
│       ├── components/  # SensorChart, AlertCard, etc.
│       ├── hooks/       # useSurveillance, useWebSocket
│       └── services/    # api.js, socketService.js
│
├── docs/                # Documentation
└── docker-compose.yml   # Orchestration
```

---

## 📚 Documentation

### Guides Complets

- **[01_SETUP.md](docs/01_SETUP.md)** - Installation détaillée
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture
- **[ML_GUIDE.md](docs/ML_GUIDE.md)** - Machine Learning

### Quick Links

📖 [Guide Installation](docs/01_SETUP.md)  
🧠 [Guide ML](docs/ML_GUIDE.md)  
🏗️ [Architecture](docs/ARCHITECTURE.md)  

---

## 🚨 Problèmes Courants

### Services ne démarrent pas

```bash
# Voir les erreurs
docker-compose logs [service]

# Rebuild
docker-compose down
docker-compose up -d --build
```

### Port déjà utilisé

```bash
# Trouver processus
netstat -ano | findstr :5000

# Tuer processus
taskkill /PID [process-id] /F
```

### Frontend ne se connecte pas

1. Vérifier Gateway: `curl http://localhost:5000/health`
2. Vérifier CORS dans `.env`: `FRONTEND_URL=http://localhost:3000`
3. Vider cache navigateur

### Modèles ML non chargés

```bash
# Vérifier fichiers
docker compose exec ml ls -la /app/models_v7/

# Relancer
docker compose restart ml
```

---

## 🧪 Tests

### Workflow Complet

```bash
# 1. Vérifier services actifs
docker-compose ps

# 2. Tester API
curl http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<SUPERADMIN_EMAIL>","password":"<SUPERADMIN_PASSWORD>"}'

# 3. Ouvrir frontend
Start-Process "http://localhost:3000"

# 4. Se connecter et vérifier:
#    - Dashboard affiche KPIs
#    - Surveillance affiche graphiques temps réel
#    - Alertes affiche historique
```

### Test Prédiction ML

```bash
# Obtenir token JWT d'abord
$token = "your-jwt-token"

# Tester prédiction moteur
curl -X POST http://localhost:5000/api/ml/predict \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "machine": "moteur",
    "sensors": {
      "vibration": 1.5,
      "current": 14.2
    }
  }'
```

---

## 🔧 Développement

### Backend (Python)

```bash
# Installer dépendances localement
cd backend/ml
pip install -r requirements.txt

# Tests
pytest

# Linter
flake8
black .
```

### Frontend (React)

```bash
cd frontend

# Installer dépendances
npm install

# Dev mode
npm run dev

# Build production
npm run build

# Vérifications statiques
npm run lint
```

---

## 📊 Monitoring

### Logs en Temps Réel

```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f ml

# Dernières 100 lignes
docker-compose logs --tail=100 ml
```

### Métriques

```bash
# Utilisation ressources
docker stats

# Espace disque
docker system df
```

---

## 🔐 Sécurité Production

### Checklist

- [ ] Changer `POSTGRES_PASSWORD` dans `.env`
- [ ] Générer nouveau `JWT_SECRET_KEY`
- [ ] Modifier mot de passe admin
- [ ] Configurer HTTPS/TLS
- [ ] Activer rate limiting
- [ ] Setup firewall
- [ ] Configurer backup automatique
- [ ] Monitoring actif

Ces éléments doivent être terminés avant tout déploiement public.

---

## 💡 Aide

### Documentation
- 📖 [docs/](docs/) - Documentation complète
- 🐛 Issues - Rapporter un bug

### Support
- Email: support@smartmaintain.com
- Documentation: [docs/README.md](docs/README.md)

---

## 🎯 Prochaines Étapes

Après installation:

1. ✅ Lire [Guide Installation](docs/01_SETUP.md)
2. ✅ Configurer `.env` correctement
3. ✅ Tester le workflow complet
4. ✅ Lire [Guide ML](docs/ML_GUIDE.md) pour entraîner modèles
5. ✅ Explorer [Architecture](docs/ARCHITECTURE.md)

---

**Version**: 2.0  
**Date**: 17 Août 2026  
**Status**: Prototype PFE — Refactorisé et simplifié pour maintenance

**Démarrage**: `docker-compose up -d` 🚀
