# 📊 MATRICES DE CONFUSION - SmartMaintain ML Models

## 📋 Vue d'Ensemble

Ce document présente les matrices de confusion et les performances détaillées des 4 modèles de Machine Learning utilisés dans SmartMaintain.

---

## 🔧 1. COMPRESSEUR (Extra Trees)

### 📈 Métriques Globales
- **Accuracy** : 92.03%
- **Precision (macro)** : 93.51%
- **Recall (macro)** : 92.03%
- **F1-Score (macro)** : 91.91%
- **Modèle** : Extra Trees

### 🎯 Performance par Classe

| Classe | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| **Fuite d'Air** | 99.74% | 76.27% | 86.44% | 5,020 |
| **Normal** | 80.79% | 99.80% | 89.30% | 5,020 |
| **Surchauffe** | 100.00% | 100.00% | 100.00% | 5,020 |

### 📊 Matrice de Confusion (approximation)

```
                        Fuite d'Air    Normal    Surchauffe
────────────────────────────────────────────────────────────
Fuite d'Air             [3,829]       1,191          0
Normal                      10        [5,010]        0  
Surchauffe                   0            0      [5,020]
────────────────────────────────────────────────────────────

Légende : [] = Prédictions correctes (diagonale)
```

### 🔬 Robustesse
- **Accuracy (propre)** : 99.34%
- **F1 (propre)** : 99.34%
- **Accuracy (bruit σ=0.2)** : 92.03%
- **F1 (bruit)** : 91.91%
- **Recall minimum** : 76.27% (Fuite d'Air)

### 💡 Analyse
✅ **Points forts** :
- Détection parfaite de la surchauffe (100%)
- Excellente précision pour détecter les fuites d'air (99.74%)

⚠️ **Points d'amélioration** :
- Le recall de "Fuite d'Air" est plus faible (76.27%) - 24% de fausses prédictions comme "Normal"
- Certaines fuites d'air sont confondues avec un fonctionnement normal

---

## ⚙️ 2. MOTEUR (Extra Trees)

### 📈 Métriques Globales
- **Accuracy** : 98.23%
- **Precision (macro)** : 98.23%
- **Recall (macro)** : 98.23%
- **F1-Score (macro)** : 98.23%
- **Modèle** : Extra Trees

### 🎯 Performance par Classe

| Classe | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| **Dégradation Roulement** | 97.88% | 96.78% | 97.33% | 5,000 |
| **Déséquilibre/Désalignement** | 100.00% | 100.00% | 100.00% | 5,000 |
| **Normal** | 96.82% | 97.90% | 97.35% | 5,000 |

### 📊 Matrice de Confusion (approximation)

```
                                Dégradation    Déséquilibre    Normal
─────────────────────────────────────────────────────────────────────
Dégradation Roulement           [4,839]            0            161
Déséquilibre/Désalignement          0          [5,000]           0
Normal                             105            0          [4,895]
─────────────────────────────────────────────────────────────────────

Légende : [] = Prédictions correctes (diagonale)
```

### 🔬 Robustesse
- **Accuracy (propre)** : 99.87%
- **F1 (propre)** : 99.87%
- **Accuracy (bruit σ=0.2)** : 98.23%
- **F1 (bruit)** : 98.23%
- **Recall minimum** : 96.78% (Dégradation Roulement)

### 💡 Analyse
✅ **Points forts** :
- Détection parfaite des déséquilibres/désalignements (100%)
- Performances très équilibrées entre toutes les classes
- Excellente robustesse au bruit

⚠️ **Points d'amélioration** :
- Légère confusion entre "Dégradation Roulement" et "Normal" (3.22%)
- Quelques faux négatifs sur la dégradation de roulement

---

## 🔄 3. ÉCHANGEUR (Random Forest)

### 📈 Métriques Globales
- **Accuracy** : 97.99%
- **Precision (macro)** : 98.05%
- **Recall (macro)** : 97.99%
- **F1-Score (macro)** : 97.99%
- **Modèle** : Random Forest

### 🎯 Performance par Classe

| Classe | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| **Encrassement** | 99.05% | 94.88% | 96.92% | 3,200 |
| **Fuite Thermique** | 100.00% | 100.00% | 100.00% | 3,200 |
| **Normal** | 95.08% | 99.09% | 97.05% | 3,200 |

### 📊 Matrice de Confusion (approximation)

```
                        Encrassement    Fuite Thermique    Normal
────────────────────────────────────────────────────────────────────
Encrassement            [3,036]              0             164
Fuite Thermique             0           [3,200]             0
Normal                     29               0           [3,171]
────────────────────────────────────────────────────────────────────

Légende : [] = Prédictions correctes (diagonale)
```

### 🔬 Robustesse
- **Accuracy (propre)** : 98.33%
- **F1 (propre)** : 98.33%
- **Accuracy (bruit σ=0.2)** : 97.99%
- **F1 (bruit)** : 97.99%
- **Recall minimum** : 94.88% (Encrassement)

### 💡 Analyse
✅ **Points forts** :
- Détection parfaite des fuites thermiques (100%)
- Très bonne robustesse au bruit
- Performances équilibrées

⚠️ **Points d'amélioration** :
- L'encrassement est parfois manqué (5.12%) et confondu avec "Normal"
- Quelques fausses alarmes d'encrassement sur fonctionnement normal

---

## 💧 4. POMPE (Random Forest)

### 📈 Métriques Globales
- **Accuracy** : 99.77%
- **Precision (macro)** : 99.77%
- **Recall (macro)** : 99.77%
- **F1-Score (macro)** : 99.77%
- **Modèle** : Random Forest

### 🎯 Performance par Classe

| Classe | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| **Cavitation** | 100.00% | 99.30% | 99.65% | 1,000 |
| **Fuite Joints** | 100.00% | 100.00% | 100.00% | 1,000 |
| **Normal** | 99.30% | 100.00% | 99.65% | 1,000 |

### 📊 Matrice de Confusion (approximation)

```
                        Cavitation    Fuite Joints    Normal
───────────────────────────────────────────────────────────────
Cavitation                [993]            0             7
Fuite Joints                0          [1,000]          0
Normal                      0              0         [1,000]
───────────────────────────────────────────────────────────────

Légende : [] = Prédictions correctes (diagonale)
```

### 🔬 Robustesse
- **Accuracy (propre)** : 100.00%
- **F1 (propre)** : 100.00%
- **Accuracy (bruit σ=0.2)** : 99.77%
- **F1 (bruit)** : 99.77%
- **Recall minimum** : 99.30% (Cavitation)

### 💡 Analyse
✅ **Points forts** :
- **Meilleur modèle de tous** (99.77% accuracy)
- Détection parfaite des fuites de joints (100%)
- Performance quasi-parfaite même avec du bruit
- Très peu de faux positifs/négatifs

⚠️ **Points d'amélioration** :
- Très légère confusion entre cavitation et normal (0.7%)
- Pratiquement aucune marge d'amélioration nécessaire !

---

## 📊 COMPARAISON GLOBALE

### Tableau Récapitulatif

| Machine | Accuracy | F1-Score | Modèle | Recall Min | Classes |
|---------|----------|----------|--------|------------|---------|
| **Pompe** 🥇 | **99.77%** | **99.77%** | Random Forest | 99.30% | 3 |
| **Moteur** 🥈 | 98.23% | 98.23% | Extra Trees | 96.78% | 3 |
| **Échangeur** 🥉 | 97.99% | 97.99% | Random Forest | 94.88% | 3 |
| **Compresseur** | 92.03% | 91.91% | Extra Trees | 76.27% | 3 |

### 📈 Visualisation des Performances

```
Accuracy par Machine
────────────────────────────────────────────────────────────
Pompe          ████████████████████████████████████ 99.77%
Moteur         ████████████████████████████████████ 98.23%
Échangeur      ███████████████████████████████████▌ 97.99%
Compresseur    ███████████████████████████████░░░░░ 92.03%
────────────────────────────────────────────────────────────
```

---

## 🔬 PROTOCOLE D'ÉVALUATION

### Méthodologie

**Protocole** : Fenêtres non-chevauchantes avec stress test d'incertitude

1. **Split de données** : Train/Test séparés temporellement
2. **Fenêtres** : Non-chevauchantes pour éviter la fuite de données
3. **Test de robustesse** :
   - Ajout de bruit gaussien (σ = 0.2)
   - 20 répétitions pour chaque test
   - Simulation de conditions réelles bruitées

### Taille des Fenêtres

| Machine | Taille Fenêtre | Raison |
|---------|----------------|--------|
| Pompe | 20 | Réponse rapide aux changements |
| Échangeur | 30 | Balance vitesse/précision |
| Compresseur | 30 | Balance vitesse/précision |
| Moteur | 100,000 | Fenêtre très large pour patterns subtils |

---

## 🎯 INTERPRÉTATION DES MÉTRIQUES

### 📖 Définitions

**Precision (Précision)** :
- Parmi toutes les prédictions positives, combien sont vraiment correctes ?
- `Precision = TP / (TP + FP)`
- ⚠️ Importance : Éviter les **fausses alarmes**

**Recall (Rappel/Sensibilité)** :
- Parmi tous les vrais positifs, combien sont détectés ?
- `Recall = TP / (TP + FN)`
- ⚠️ Importance : Éviter les **pannes manquées**

**F1-Score** :
- Moyenne harmonique de Precision et Recall
- `F1 = 2 × (Precision × Recall) / (Precision + Recall)`
- ⚠️ Importance : **Balance** entre les deux

### 🎭 Cas d'Usage

**Haute Precision requise** :
- Éviter les arrêts de production inutiles
- Coût élevé des interventions de maintenance
- → Focus : Minimiser les fausses alarmes

**Haut Recall requis** :
- Équipements critiques pour la sécurité
- Coût très élevé des pannes
- → Focus : Détecter TOUTES les anomalies

**Balance F1-Score** :
- SmartMaintain vise un **équilibre optimal**
- Détecter les pannes SANS trop de fausses alarmes

---

## 🚨 SEUILS DE RISQUE

### Classification par Niveau de Risque

```python
if failure_risk > 70%:
    severity = "CRITICAL"    # Alerte rouge
elif failure_risk > 40%:
    severity = "WARNING"     # Alerte orange
else:
    severity = "NORMAL"      # Vert (pas d'alerte)
```

### Recommandations par Classe

| Machine | Classe Détectée | Recommendation |
|---------|----------------|----------------|
| **Compresseur** | Fuite d'Air | Vérifier joints et vannes |
| | Surchauffe | Contrôler système de refroidissement |
| **Moteur** | Dégradation Roulement | Remplacer roulements |
| | Déséquilibre | Équilibrage et alignement |
| **Échangeur** | Encrassement | Nettoyage tubes échangeur |
| | Fuite Thermique | Vérifier étanchéité circuits |
| **Pompe** | Cavitation | Vérifier pression d'aspiration |
| | Fuite Joints | Remplacer joints d'étanchéité |

---

## 🔄 WORKFLOW DE PRÉDICTION

```
┌──────────────────┐
│  Données Capteur │ (température, vibration, pression, etc.)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Feature Engineer │ (20+ features : stats, FFT, rolling windows)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Modèle ML        │ (Random Forest ou Extra Trees)
│ Par Machine      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Prédiction       │
├──────────────────┤
│ • failure_risk   │ (0-100%)
│ • predicted_class│ (normal/warning/critical)
│ • days_to_failure│ (estimation)
│ • recommendation │ (texte)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Alerte + WebSocket│ (si risque > 40%)
└──────────────────┘
```

---

## 📁 FICHIERS SOURCES

Les métriques brutes sont disponibles dans :
```
backend/ml/models_v7/
├── compresseur/
│   ├── metrics.json      ← Métriques détaillées
│   ├── metadata.json     ← Info modèle
│   └── model.pkl         ← Modèle entraîné
├── moteur/
│   ├── metrics.json
│   ├── metadata.json
│   └── model.pkl
├── echangeur/
│   ├── metrics.json
│   ├── metadata.json
│   └── model.pkl
└── pompe/
    ├── metrics.json
    ├── metadata.json
    └── model.pkl
```

---

## 🎓 CONCLUSION

### Points Clés

✅ **Excellentes performances globales** : Tous les modèles > 92% accuracy  
✅ **Pompe = champion** : 99.77% accuracy (quasi-parfait)  
✅ **Robustesse validée** : Bonne résistance au bruit (σ=0.2)  
✅ **Production-ready** : Métriques suffisantes pour déploiement  

### Pistes d'Amélioration

1. **Compresseur (priorité haute)** :
   - Améliorer le recall de "Fuite d'Air" (actuellement 76.27%)
   - Collecter plus de données de fuites d'air
   - Ajuster les features de détection

2. **Tous les modèles** :
   - Monitoring continu des performances en production
   - Réentraînement périodique avec nouvelles données
   - A/B testing de nouvelles architectures

3. **Métriques additionnelles** :
   - Temps de détection moyen
   - Coût des fausses alarmes vs pannes manquées
   - ROI de la maintenance prédictive

---

**Document généré le** : 7 septembre 2026  
**Version modèles** : v7  
**Auteur** : SmartMaintain ML Team
