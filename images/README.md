# 📊 Images et Figures du Rapport PFE

Ce dossier contient toutes les figures utilisées dans le rapport de PFE.

## 🎯 Figures Manquantes à Générer

### 1. Matrices de Confusion (`matrices-confusion-modeles.png`)
**Contenu** : Grille 2x2 avec les 4 matrices de confusion (Pompe, Moteur, Compresseur, Échangeur)

**Pour générer** :
```bash
# Démarrer Docker Desktop d'abord
docker-compose up -d

# Installer les dépendances et générer
docker exec -it smartmaintain-ml-1 bash -c "pip install matplotlib seaborn && python generate_report_figures.py"
```

### 2. Graphique de Robustesse (`robustesse-modeles.png`)
**Contenu** : Graphique en barres comparant l'accuracy avec et sans bruit pour chaque modèle

**Génération** : Le même script génère les deux figures automatiquement

---

## 📝 Génération Manuelle (si Docker ne fonctionne pas)

Si vous avez Python installé localement :

```bash
# 1. Aller dans le dossier ML
cd "c:\Users\Mohamed Sadok\Desktop\PFE Maintenance prédictive\smartmaintain\backend\ml"

# 2. Installer les dépendances
pip install matplotlib seaborn numpy

# 3. Exécuter le script
python generate_report_figures.py
```

---

## 📁 Fichiers Générés

Après exécution du script, vous aurez :

```
images/
├── matrices-confusion-modeles.png    ← Chapitre 4
├── robustesse-modeles.png            ← Chapitre 4
└── metriques-modeles.txt             ← Résumé textuel
```

---

## 🔍 Captures d'Écran Existantes (Chapitre 5)

Les captures suivantes sont déjà présentes :

1. **Page de connexion** - Interface d'authentification
2. **Dashboard principal** - Vue d'ensemble avec KPIs
3. **Page surveillance** - Monitoring temps réel
4. **Page alertes** - Liste et gestion des alertes
5. **Détail alerte** - Informations complètes d'une alerte
6. **Gestion composants** - CRUD des équipements

---

## 📊 Données Sources

Les matrices de confusion sont générées à partir des métriques réelles stockées dans :

```
backend/ml/models_v7/
├── pompe/metrics.json
├── moteur/metrics.json
├── compresseur/metrics.json
└── echangeur/metrics.json
```

### Résumé des Performances

| Machine | Accuracy | F1-Score | Modèle |
|---------|----------|----------|--------|
| Pompe | 99.77% | 99.77% | Random Forest |
| Moteur | 98.23% | 98.23% | Extra Trees |
| Échangeur | 97.99% | 97.99% | Random Forest |
| Compresseur | 92.03% | 91.91% | Extra Trees |

---

## ⚠️ Troubleshooting

### Erreur : `ModuleNotFoundError: No module named 'matplotlib'`

**Solution** :
```bash
docker exec -it smartmaintain-ml-1 pip install matplotlib seaborn
```

### Erreur : Docker Desktop n'est pas démarré

**Solution** :
1. Démarrer Docker Desktop manuellement
2. Attendre que l'icône soit stable (10-20 secondes)
3. Relancer la commande

### Erreur : Permission denied

**Solution** :
```bash
# Donner les permissions
chmod +x backend/ml/generate_report_figures.py
```

---

## 📞 Support

Pour toute question sur la génération des figures, consulter :
- `CONFUSION_MATRICES.md` - Documentation complète des métriques
- `backend/ml/generate_report_figures.py` - Code source du générateur

---

**Dernière mise à jour** : 8 septembre 2026
