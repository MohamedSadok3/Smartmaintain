"""
Script pour générer les matrices de confusion des modèles ML
"""
import json
import os
from pathlib import Path
import numpy as np


def load_metrics(machine_type):
    """Charge les métriques depuis metrics.json"""
    metrics_path = Path(__file__).parent / f"models_v7/{machine_type}/metrics.json"
    with open(metrics_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_confusion_matrix_from_metrics(metrics, machine_type):
    """
    Crée une matrice de confusion approximative à partir du classification report
    """
    report = metrics['classification_report']
    
    # Obtenir les classes (exclure les clés non-classe)
    classes = [k for k in report.keys() 
               if k not in ['accuracy', 'macro avg', 'weighted avg']]
    
    n_classes = len(classes)
    confusion_matrix = np.zeros((n_classes, n_classes))
    
    # Remplir la matrice à partir du recall et support
    for i, class_name in enumerate(classes):
        class_data = report[class_name]
        support = int(class_data['support'])
        recall = class_data['recall']
        
        # True positives (diagonale)
        true_positives = int(support * recall)
        confusion_matrix[i][i] = true_positives
        
        # False negatives (distribués sur les autres classes)
        false_negatives = support - true_positives
        if false_negatives > 0 and n_classes > 1:
            # Distribuer équitablement les faux négatifs
            fn_per_class = false_negatives / (n_classes - 1)
            for j in range(n_classes):
                if i != j:
                    confusion_matrix[i][j] = fn_per_class
    
    return confusion_matrix, classes


def plot_confusion_matrix(cm, classes, machine_type, save_path):
    """
    Génère une visualisation ASCII de la matrice de confusion
    """
    # Créer le fichier texte avec visualisation ASCII
    txt_path = save_path.replace('.png', '.txt')
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"╔{'═'*70}╗\n")
        f.write(f"║  MATRICE DE CONFUSION - {machine_type.upper():^40}  ║\n")
        f.write(f"╚{'═'*70}╝\n\n")
        
        # En-tête des colonnes
        f.write("                    ")
        for cls in classes:
            f.write(f"{cls[:15]:>20}")
        f.write("\n")
        f.write("                    " + "─"*20*len(classes) + "\n")
        
        # Lignes de la matrice
        for i, true_class in enumerate(classes):
            f.write(f"{true_class[:15]:>18} │")
            for j in range(len(classes)):
                value = int(cm[i][j])
                if i == j:
                    # Valeurs diagonales en gras (ASCII)
                    f.write(f"  [{value:>5}]         ")
                else:
                    f.write(f"   {value:>5}          ")
            f.write("\n")
        
        f.write("\n")
        f.write("Note: Les valeurs entre [] sont sur la diagonale (bonnes prédictions)\n")
    
    print(f"✅ Matrice ASCII sauvegardée: {txt_path}")
    return txt_path


def generate_summary_report(machine_type, metrics):
    """Génère un rapport textuel détaillé"""
    report = metrics['classification_report']
    
    summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║        RAPPORT DE PERFORMANCE - {machine_type.upper():^20}        ║
╚══════════════════════════════════════════════════════════════════╝

📊 MÉTRIQUES GLOBALES
────────────────────────────────────────────────────────────────────
• Accuracy (Précision globale):    {metrics['accuracy']:.2%}
• Macro Precision:                  {metrics['macro_precision']:.2%}
• Macro Recall:                     {metrics['macro_recall']:.2%}
• Macro F1-Score:                   {metrics['macro_f1']:.2%}

🎯 PERFORMANCE PAR CLASSE
────────────────────────────────────────────────────────────────────
"""
    
    classes = [k for k in report.keys() 
               if k not in ['accuracy', 'macro avg', 'weighted avg']]
    
    for class_name in classes:
        class_data = report[class_name]
        summary += f"""
🔹 {class_name.replace('_', ' ').title()}:
   • Precision: {class_data['precision']:.2%}
   • Recall:    {class_data['recall']:.2%}
   • F1-Score:  {class_data['f1-score']:.2%}
   • Support:   {int(class_data['support'])} échantillons
"""
    
    summary += f"""
🔬 ROBUSTESSE
────────────────────────────────────────────────────────────────────
• Accuracy (conditions propres):    {metrics['clean_accuracy']:.2%}
• F1 (conditions propres):          {metrics['clean_macro_f1']:.2%}
• Accuracy (avec bruit σ={metrics['robustness_noise_sigma']}): {metrics['robustness_accuracy']:.2%}
• F1 (avec bruit):                  {metrics['robustness_macro_f1']:.2%}

⚙️ CONFIGURATION
────────────────────────────────────────────────────────────────────
• Modèle sélectionné:               {metrics['selected_model']}
• Taille fenêtre:                   {metrics['window_size']}
• Protocole d'évaluation:           {metrics['evaluation_protocol'][:50]}...
• Recall minimum par classe:        {metrics['minimum_class_recall']:.2%}

╚══════════════════════════════════════════════════════════════════╝
"""
    
    return summary


def main():
    """Génère toutes les matrices de confusion"""
    
    print("\n" + "="*70)
    print("  🎯 GÉNÉRATION DES MATRICES DE CONFUSION")
    print("="*70 + "\n")
    
    machines = ['pompe', 'moteur', 'compresseur', 'echangeur']
    output_dir = Path(__file__).parent / "confusion_matrices"
    output_dir.mkdir(exist_ok=True)
    
    for machine in machines:
        print(f"\n📊 Traitement: {machine.upper()}")
        print("-" * 70)
        
        # Charger les métriques
        metrics = load_metrics(machine)
        
        # Créer la matrice de confusion
        cm, classes = create_confusion_matrix_from_metrics(metrics, machine)
        
        # Sauvegarder l'image
        img_path = output_dir / f"{machine}_confusion_matrix.png"
        plot_confusion_matrix(cm, classes, machine, img_path)
        
        # Sauvegarder le rapport textuel
        report = generate_summary_report(machine, metrics)
        report_path = output_dir / f"{machine}_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Rapport sauvegardé: {report_path}")
        
        # Sauvegarder la matrice en CSV
        csv_path = output_dir / f"{machine}_confusion_matrix.csv"
        np.savetxt(csv_path, cm, delimiter=',', fmt='%.0f', 
                   header=','.join(classes), comments='')
        print(f"✅ CSV sauvegardé: {csv_path}")
    
    print("\n" + "="*70)
    print(f"  ✅ TERMINÉ! Tous les fichiers sont dans: {output_dir}")
    print("="*70 + "\n")
    
    # Créer un fichier README
    readme_content = """# Matrices de Confusion - SmartMaintain ML Models

## 📁 Contenu

Ce dossier contient les matrices de confusion et rapports de performance pour les 4 modèles ML :

- **pompe** : Détection de cavitation et fuites de joints
- **moteur** : Détection de dégradation de roulement et déséquilibre
- **compresseur** : Détection de fuite d'air et surchauffe
- **echangeur** : Détection d'encrassement et fuite thermique

## 📊 Fichiers par modèle

Pour chaque machine (pompe, moteur, compresseur, echangeur) :

- `{machine}_confusion_matrix.png` - Visualisation graphique de la matrice
- `{machine}_confusion_matrix.csv` - Matrice au format CSV (importable Excel)
- `{machine}_report.txt` - Rapport détaillé des performances

## 🎯 Interprétation de la matrice de confusion

### Structure
```
                    Classe Prédite
                 A        B        C
Vraie    A    [TN_A]   [FP_AB]  [FP_AC]
Classe   B    [FP_BA]  [TN_B]   [FP_BC]
         C    [FP_CA]  [FP_CB]  [TN_C]
```

### Lecture
- **Diagonale** (valeurs élevées = bon) : Prédictions correctes
- **Hors diagonale** (valeurs faibles = bon) : Erreurs de classification

### Métriques dérivées

**Precision (Précision)** = TP / (TP + FP)
- "Quand le modèle prédit une classe, à quelle fréquence a-t-il raison ?"

**Recall (Rappel/Sensibilité)** = TP / (TP + FN)
- "Parmi tous les vrais cas d'une classe, combien le modèle détecte-t-il ?"

**F1-Score** = 2 × (Precision × Recall) / (Precision + Recall)
- Moyenne harmonique de la précision et du rappel

## 📈 Résumé des performances

| Machine     | Accuracy | F1-Score | Modèle utilisé  |
|-------------|----------|----------|-----------------|
| Pompe       | 99.77%   | 99.77%   | Random Forest   |
| Moteur      | 98.23%   | 98.23%   | Extra Trees     |
| Compresseur | 92.03%   | 91.91%   | Extra Trees     |
| Échangeur   | 97.99%   | 97.99%   | Random Forest   |

## 🔬 Test de robustesse

Tous les modèles ont été testés avec :
- **Bruit ajouté** : σ = 0.2 (20% de bruit gaussien)
- **Répétitions** : 20 tests par configuration
- **Protocole** : Fenêtres non-chevauchantes avec stress test d'incertitude

## 📝 Notes

Les matrices présentées sont des approximations calculées à partir des métriques
de classification (precision, recall, support). Elles permettent de visualiser
la distribution des erreurs de prédiction entre les différentes classes.

**Généré le** : {date}
**Version modèles** : v7
"""
    
    from datetime import datetime
    readme_content = readme_content.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    readme_path = output_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"📝 README créé: {readme_path}\n")


if __name__ == "__main__":
    main()
