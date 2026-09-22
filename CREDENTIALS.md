# 🔐 CREDENTIALS - SmartMaintain Demo

## 🌐 Accès à l'Application

**URL Frontend :** http://localhost:3000  
**URL API Gateway :** http://localhost:5000

---

## 👤 COMPTES DE DÉMONSTRATION

### 🔴 SuperAdmin (Accès Total)

```
📧 Email:    sado9m3@gmail.com
🔑 Password: superadmin123456
```

**Permissions :**
- ✅ Gestion de toutes les usines
- ✅ Approbation des inscriptions
- ✅ Création/modification/suppression d'utilisateurs (tous rôles)
- ✅ Accès à toutes les alertes (multi-tenant)
- ✅ Configuration système globale
- ✅ Vue d'ensemble multi-usines

**Pages accessibles :**
- `/dashboard` - Vue d'ensemble globale
- `/plants` - Gestion des usines
- `/registrations` - Approbation des demandes d'inscription
- `/utilisateurs` - Gestion de tous les utilisateurs
- `/composants` - Tous les composants de toutes les usines
- `/alertes` - Toutes les alertes de toutes les usines
- `/surveillance` - Monitoring temps réel global

---

### 🟢 Admin (Accès Usine)

**Note :** Aucun compte admin n'est créé par défaut. Vous devez en créer un via le SuperAdmin.

**Comment créer un Admin :**
1. Connectez-vous en tant que SuperAdmin
2. Allez dans `/utilisateurs`
3. Cliquez sur "Ajouter un utilisateur"
4. Remplissez :
   - Email : `admin@usine1.com`
   - Mot de passe : `admin123`
   - Rôle : `Admin`
   - Usine : Sélectionnez une usine existante

**Permissions :**
- ✅ Gestion des utilisateurs de son usine (operators)
- ✅ Création/modification/suppression de composants de son usine
- ✅ Gestion des alertes de son usine
- ✅ Configuration IoT de son usine
- ❌ Ne peut PAS voir les autres usines
- ❌ Ne peut PAS créer d'autres admins

---

### 🔵 Operator (Consultation)

**Note :** Aucun compte operator n'est créé par défaut.

**Comment créer un Operator :**
1. Connectez-vous en tant que SuperAdmin ou Admin
2. Allez dans `/utilisateurs`
3. Créez un utilisateur avec le rôle `Operator`

**Permissions :**
- ✅ Consultation du dashboard de son usine
- ✅ Consultation des alertes de son usine
- ✅ Consultation des composants de son usine
- ✅ Surveillance temps réel
- ❌ Aucune modification (lecture seule)

---

## 🏢 USINES (PLANTS) PAR DÉFAUT

Aucune usine n'est créée par défaut. Vous devez :

### Option 1 : Inscription Publique
1. Allez sur http://localhost:3000
2. Cliquez sur "S'inscrire"
3. Remplissez le formulaire d'inscription d'usine
4. Attendez l'approbation du SuperAdmin

### Option 2 : Création Directe (SuperAdmin)
1. Connectez-vous en tant que SuperAdmin
2. Allez dans `/plants`
3. Créez une nouvelle usine manuellement

---

## 📧 CONFIGURATION EMAIL

**Provider :** SMTP (Gmail)  
**From Email :** `sadokm3@gmail.com`

**Credentials SMTP :**
- **Host :** smtp.gmail.com
- **Port :** 587
- **Username :** sadokm3@gmail.com
- **Password :** `owgu zwbz objq tqym` (App Password)

**Note :** Les emails sont envoyés pour :
- Inscription d'une nouvelle usine (notification au SuperAdmin)
- Approbation d'inscription (notification à l'admin de l'usine)
- Alertes critiques (si configuré)

---

## 🗄️ BASE DE DONNÉES

### PostgreSQL

**Host :** `localhost` (ou `postgres` dans Docker)  
**Port :** `5432`  
**Database :** `smartmaintain`  
**User :** `admin`  
**Password :** `secret`

**Connection String :**
```
postgresql://admin:secret@postgres:5432/smartmaintain
```

**Accès direct :**
```bash
docker exec -it smartmaintain-postgres-1 psql -U admin -d smartmaintain
```

### Redis

**Host :** `localhost` (ou `redis` dans Docker)  
**Port :** `6379`  
**Password :** Aucun

**Accès direct :**
```bash
docker exec -it smartmaintain-redis-1 redis-cli
```

**Channels à surveiller :**
- `sensor_data_raw` - Données IoT brutes
- `ml_predictions` - Prédictions ML

---

## 🔧 CRÉATION D'UTILISATEURS POUR DÉMO

### Script SQL pour créer des utilisateurs de test

```sql
-- Se connecter à PostgreSQL
-- docker exec -it smartmaintain-postgres-1 psql -U admin -d smartmaintain

-- Créer une usine de test
INSERT INTO plants (name, address, city, country, admin_email, status, approved_at)
VALUES ('Usine Test Paris', '123 Rue de Test', 'Paris', 'France', 'admin@test.fr', 'approved', NOW())
RETURNING id; -- Notez l'ID retourné (ex: 1)

-- Créer un Admin pour cette usine
-- Mot de passe : admin123
INSERT INTO users (first_name, last_name, email, password_hash, role, plant_id, is_active)
VALUES (
    'Admin',
    'Test',
    'admin@test.fr',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztP6LbUvnWKe',
    'admin',
    1, -- Remplacer par l'ID de votre usine
    TRUE
);

-- Créer un Operator pour cette usine
-- Mot de passe : operator123
INSERT INTO users (first_name, last_name, email, password_hash, role, plant_id, is_active)
VALUES (
    'Operator',
    'Test',
    'operator@test.fr',
    '$2b$12$eCvHvMrfGNu8L4pEQxPKxOQFy8YhWZX.YgVKyNQP8qWLM0RxKGVXa',
    'operator',
    1, -- Remplacer par l'ID de votre usine
    TRUE
);

-- Créer des composants pour l'usine
INSERT INTO components (plant_id, name, machine_type, location, installation_date, status)
VALUES
    (1, 'Pompe #1', 'pompe', 'Atelier A', '2024-01-01', 'active'),
    (1, 'Moteur #1', 'moteur', 'Atelier B', '2024-01-01', 'active'),
    (1, 'Compresseur #1', 'compresseur', 'Atelier C', '2024-01-01', 'active'),
    (1, 'Échangeur #1', 'echangeur', 'Atelier D', '2024-01-01', 'active');
```

---

## 🎯 WORKFLOW DE TEST COMPLET

### 1️⃣ Connexion SuperAdmin
```
URL: http://localhost:3000
Email: sado9m3@gmail.com
Password: superadmin123456
```

### 2️⃣ Créer une Usine
- Allez dans `/plants`
- Cliquez sur "Ajouter une usine"
- Remplissez les informations
- Status : `approved`

### 3️⃣ Créer un Admin pour l'Usine
- Allez dans `/utilisateurs`
- Cliquez sur "Ajouter un utilisateur"
- Email : `admin@usine1.com`
- Rôle : `Admin`
- Usine : Sélectionnez l'usine créée
- Mot de passe : `admin123`

### 4️⃣ Créer des Composants
- Allez dans `/composants`
- Créez plusieurs composants (pompe, moteur, compresseur, échangeur)

### 5️⃣ Activer le Replay IoT
- Le service IoT démarre automatiquement
- Il envoie des données toutes les 2 secondes
- Les prédictions ML sont générées automatiquement
- Les alertes sont créées si le risque > 70%

### 6️⃣ Surveiller en Temps Réel
- Allez dans `/surveillance`
- Observez les données en temps réel via WebSocket
- Les graphs se mettent à jour automatiquement

### 7️⃣ Gérer les Alertes
- Allez dans `/alertes`
- Consultez les alertes générées
- Cliquez sur une alerte pour la prendre en charge
- Changez le statut : `pending` → `acknowledged` → `resolved`

---

## 🔑 HASH DES MOTS DE PASSE

**Pour générer un nouveau hash bcrypt :**

```python
import bcrypt

password = "votre_mot_de_passe"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
print(hashed.decode('utf-8'))
```

**Ou en ligne de commande :**
```bash
docker exec -it smartmaintain-auth-1 python3 -c "import bcrypt; print(bcrypt.hashpw(b'votre_mot_de_passe', bcrypt.gensalt(12)).decode())"
```

---

## ⚠️ SÉCURITÉ - IMPORTANT

### 🚨 À FAIRE EN PRODUCTION

1. **Changer le JWT_SECRET**
   ```env
   JWT_SECRET=générer-une-clé-aléatoire-longue-et-sécurisée
   ```

2. **Changer les identifiants PostgreSQL**
   ```env
   POSTGRES_USER=votre_user
   POSTGRES_PASSWORD=mot_de_passe_fort_123!@#
   ```

3. **Changer le mot de passe SuperAdmin**
   - Connectez-vous
   - Allez dans `/profile`
   - Changez le mot de passe

4. **Configurer HTTPS**
   - Utilisez un reverse proxy (nginx, traefik)
   - Certificats SSL/TLS

5. **Activer le Rate Limiting**
   - Limiter les tentatives de login
   - Protection DDoS

6. **Logs & Monitoring**
   - Configurer ELK Stack ou Grafana
   - Alertes de sécurité

---

## 📞 SUPPORT

**En cas de problème :**

1. Vérifier que tous les services sont running :
   ```bash
   docker ps
   ```

2. Consulter les logs :
   ```bash
   docker-compose logs -f
   ```

3. Réinitialiser la base de données :
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

4. Vérifier l'état des migrations :
   ```bash
   docker-compose logs migrations
   ```

---

**Dernière mise à jour :** 7 septembre 2026  
**Version :** 1.0
