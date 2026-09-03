"""
Génération de données CSV réalistes pour tous les composants
==============================================================
Ce script génère des données temps réel pour:
- Moteur électrique (vibration, current, temperature)
- Pompe hydraulique (vibration, pressure_in, pressure_out, flow_rate)
- Compresseur d'air (pressure, current, temperature_oil, temperature_air)
- Échangeur thermique (temp_in_hot, temp_out_hot, temp_in_cold, temp_out_cold, flow_rate)

Avec injection de défauts réalistes pour démonstration
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


class DataGenerator:
    """Générateur de données capteurs réalistes avec défauts"""
    
    def __init__(self, n_samples=500, interval_seconds=60):
        self.n_samples = n_samples
        self.interval_seconds = interval_seconds
        self.start_time = datetime(2025, 1, 1, 0, 0, 0)
        
    def generate_timestamps(self):
        """Génère timestamps séquentiels"""
        return [
            (self.start_time + timedelta(seconds=i * self.interval_seconds)).isoformat()
            for i in range(self.n_samples)
        ]


class MoteurGenerator(DataGenerator):
    """Générateur données Moteur Électrique"""
    
    def generate_normal(self):
        """Fonctionnement normal"""
        timestamps = self.generate_timestamps()
        
        # Vibration normale: 0.2-0.4 g
        vibration = 0.3 + np.random.normal(0, 0.05, self.n_samples)
        vibration = np.clip(vibration, 0.15, 0.5)
        
        # Courant normal: 10-15 A
        current = 12.5 + np.random.normal(0, 1.5, self.n_samples)
        current = np.clip(current, 8, 18)
        
        # Température normale: 60-80°C
        temperature = 70 + np.random.normal(0, 5, self.n_samples)
        temperature = np.clip(temperature, 55, 95)
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'vibration': vibration,
            'current': current,
            'temperature': temperature
        })
    
    def inject_bearing_fault(self, df, start_idx=350, severity=2.0):
        """Inject défaut roulement (augmente vibration)"""
        fault_length = len(df) - start_idx
        ramp = np.linspace(1.0, severity, fault_length)
        df.loc[start_idx:, 'vibration'] *= ramp
        df.loc[start_idx:, 'temperature'] += np.linspace(0, 15, fault_length)
        return df
    
    def inject_imbalance(self, df, start_idx=250, severity=1.5):
        """Inject déséquilibre (vibration périodique)"""
        fault_length = len(df) - start_idx
        periodic = np.sin(np.linspace(0, 10*np.pi, fault_length))
        df.loc[start_idx:, 'vibration'] += periodic * 0.2 * severity
        df.loc[start_idx:, 'current'] += np.abs(periodic) * 2
        return df
    
    def generate_with_faults(self):
        """Génère dataset avec défauts réalistes"""
        df = self.generate_normal()
        
        # 70% normal, puis défauts progressifs
        normal_idx = int(self.n_samples * 0.7)
        
        # Déséquilibre léger
        df = self.inject_imbalance(df, normal_idx, severity=1.3)
        
        # Dégradation roulement plus tard
        bearing_idx = int(self.n_samples * 0.85)
        df = self.inject_bearing_fault(df, bearing_idx, severity=1.8)
        
        return df


class PompeGenerator(DataGenerator):
    """Générateur données Pompe Hydraulique"""
    
    def generate_normal(self):
        """Fonctionnement normal"""
        timestamps = self.generate_timestamps()
        
        # Vibration normale: 0.2-0.3 g
        vibration = 0.25 + np.random.normal(0, 0.03, self.n_samples)
        
        # Pression entrée: 2-4 bar
        pressure_in = 3.0 + np.random.normal(0, 0.3, self.n_samples)
        pressure_in = np.clip(pressure_in, 1.5, 5)
        
        # Pression sortie: 8-12 bar
        pressure_out = 10.0 + np.random.normal(0, 0.8, self.n_samples)
        pressure_out = np.clip(pressure_out, 7, 14)
        
        # Débit: 100-120 L/min
        flow_rate = 110 + np.random.normal(0, 5, self.n_samples)
        flow_rate = np.clip(flow_rate, 90, 130)
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'vibration': vibration,
            'pressure_in': pressure_in,
            'pressure_out': pressure_out,
            'flow_rate': flow_rate
        })
    
    def inject_cavitation(self, df, start_idx=300, severity=2.5):
        """Inject cavitation (vibration erratique, perte pression)"""
        fault_length = len(df) - start_idx
        
        # Vibration augmente avec oscillations
        noise = np.random.normal(0, 0.1 * severity, fault_length)
        df.loc[start_idx:, 'vibration'] *= (1 + severity * 0.5)
        df.loc[start_idx:, 'vibration'] += np.abs(noise)
        
        # Perte de pression sortie
        df.loc[start_idx:, 'pressure_out'] *= np.linspace(1.0, 0.75, fault_length)
        
        # Débit instable
        df.loc[start_idx:, 'flow_rate'] += np.random.normal(0, 15, fault_length)
        
        return df
    
    def inject_seal_wear(self, df, start_idx=380, severity=1.5):
        """Inject usure garniture (fuite, perte efficacité)"""
        fault_length = len(df) - start_idx
        
        # Pression sortie diminue
        df.loc[start_idx:, 'pressure_out'] -= np.linspace(0, 2 * severity, fault_length)
        
        # Débit diminue
        df.loc[start_idx:, 'flow_rate'] -= np.linspace(0, 15 * severity, fault_length)
        
        # Vibration augmente légèrement
        df.loc[start_idx:, 'vibration'] *= np.linspace(1.0, 1.3, fault_length)
        
        return df
    
    def generate_with_faults(self):
        """Génère dataset avec défauts"""
        df = self.generate_normal()
        
        # Cavitation vers 60%
        df = self.inject_cavitation(df, int(self.n_samples * 0.6), severity=2.0)
        
        # Usure garniture vers 76%
        df = self.inject_seal_wear(df, int(self.n_samples * 0.76), severity=1.5)
        
        return df


class CompresseurGenerator(DataGenerator):
    """Générateur données Compresseur d'Air"""
    
    def generate_normal(self):
        """Fonctionnement normal"""
        timestamps = self.generate_timestamps()
        
        # Pression air: 7-9 bar
        pressure = 8.0 + np.random.normal(0, 0.5, self.n_samples)
        pressure = np.clip(pressure, 6, 10)
        
        # Courant: 15-20 A
        current = 17.5 + np.random.normal(0, 1.0, self.n_samples)
        current = np.clip(current, 14, 22)
        
        # Température huile: 60-75°C
        temperature_oil = 67.5 + np.random.normal(0, 3, self.n_samples)
        temperature_oil = np.clip(temperature_oil, 55, 85)
        
        # Température air: 30-45°C
        temperature_air = 37.5 + np.random.normal(0, 3, self.n_samples)
        temperature_air = np.clip(temperature_air, 25, 55)
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'pressure': pressure,
            'current': current,
            'temperature_oil': temperature_oil,
            'temperature_air': temperature_air
        })
    
    def inject_valve_wear(self, df, start_idx=320, severity=1.8):
        """Inject usure soupapes (perte pression, courant augmente)"""
        fault_length = len(df) - start_idx
        
        # Pression diminue
        df.loc[start_idx:, 'pressure'] -= np.linspace(0, 1.5 * severity, fault_length)
        
        # Courant augmente (effort)
        df.loc[start_idx:, 'current'] += np.linspace(0, 3 * severity, fault_length)
        
        # Températures augmentent
        df.loc[start_idx:, 'temperature_oil'] += np.linspace(0, 12, fault_length)
        df.loc[start_idx:, 'temperature_air'] += np.linspace(0, 8, fault_length)
        
        return df
    
    def inject_cooling_issue(self, df, start_idx=400, severity=2.0):
        """Inject problème refroidissement huile"""
        fault_length = len(df) - start_idx
        
        # Température huile monte rapidement
        df.loc[start_idx:, 'temperature_oil'] += np.linspace(0, 20 * severity, fault_length)
        
        # Température air aussi
        df.loc[start_idx:, 'temperature_air'] += np.linspace(0, 10, fault_length)
        
        # Courant augmente
        df.loc[start_idx:, 'current'] += np.linspace(0, 2, fault_length)
        
        return df
    
    def generate_with_faults(self):
        """Génère dataset avec défauts"""
        df = self.generate_normal()
        
        # Usure soupapes vers 64%
        df = self.inject_valve_wear(df, int(self.n_samples * 0.64), severity=1.5)
        
        # Problème refroidissement vers 80%
        df = self.inject_cooling_issue(df, int(self.n_samples * 0.80), severity=1.8)
        
        return df


class EchangeurGenerator(DataGenerator):
    """Générateur données Échangeur Thermique"""
    
    def generate_normal(self):
        """Fonctionnement normal"""
        timestamps = self.generate_timestamps()
        
        # Fluide chaud: 80°C → 45°C
        temp_in_hot = 80 + np.random.normal(0, 2, self.n_samples)
        temp_out_hot = 45 + np.random.normal(0, 1.5, self.n_samples)
        
        # Fluide froid: 15°C → 35°C
        temp_in_cold = 15 + np.random.normal(0, 1, self.n_samples)
        temp_out_cold = 35 + np.random.normal(0, 1.5, self.n_samples)
        
        # Débit: 100 L/min
        flow_rate = 100 + np.random.normal(0, 5, self.n_samples)
        flow_rate = np.clip(flow_rate, 85, 115)
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'temp_in_hot': temp_in_hot,
            'temp_out_hot': temp_out_hot,
            'temp_in_cold': temp_in_cold,
            'temp_out_cold': temp_out_cold,
            'flow_rate': flow_rate
        })
    
    def inject_fouling(self, df, start_idx=280, severity=2.0):
        """Inject encrassement progressif (perte efficacité)"""
        fault_length = len(df) - start_idx
        
        # Efficacité diminue: sortie chaude plus haute
        df.loc[start_idx:, 'temp_out_hot'] += np.linspace(0, 8 * severity, fault_length)
        
        # Sortie froide plus basse (moins de chaleur transférée)
        df.loc[start_idx:, 'temp_out_cold'] -= np.linspace(0, 5 * severity, fault_length)
        
        return df
    
    def inject_internal_leak(self, df, start_idx=400, severity=1.5):
        """Inject fuite interne (mélange fluides)"""
        fault_length = len(df) - start_idx
        
        # Températures convergent (mélange)
        leak_effect = np.linspace(0, 5 * severity, fault_length)
        df.loc[start_idx:, 'temp_out_hot'] -= leak_effect
        df.loc[start_idx:, 'temp_out_cold'] += leak_effect * 0.8
        
        # Débit instable
        df.loc[start_idx:, 'flow_rate'] += np.random.normal(0, 10, fault_length)
        
        return df
    
    def generate_with_faults(self):
        """Génère dataset avec défauts"""
        df = self.generate_normal()
        
        # Encrassement vers 56%
        df = self.inject_fouling(df, int(self.n_samples * 0.56), severity=1.8)
        
        # Fuite interne vers 80%
        df = self.inject_internal_leak(df, int(self.n_samples * 0.80), severity=1.5)
        
        return df


def main():
    """Génère tous les fichiers CSV"""
    print("🔧 Génération données CSV pour SmartMaintain\n")
    print("=" * 60)
    
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Moteur
    print("\n⚙️  MOTEUR ÉLECTRIQUE")
    print("-" * 60)
    moteur_gen = MoteurGenerator(n_samples=500)
    df_moteur = moteur_gen.generate_with_faults()
    output_moteur = data_dir / "moteur.csv"
    df_moteur.to_csv(output_moteur, index=False, float_format='%.4f')
    print(f"✅ Créé: {output_moteur}")
    print(f"   Lignes: {len(df_moteur)}")
    print(f"   Colonnes: {', '.join(df_moteur.columns[1:])}")
    print(f"   Vibration: {df_moteur['vibration'].min():.3f} - {df_moteur['vibration'].max():.3f} g")
    print(f"   Courant: {df_moteur['current'].min():.1f} - {df_moteur['current'].max():.1f} A")
    print(f"   Température: {df_moteur['temperature'].min():.1f} - {df_moteur['temperature'].max():.1f} °C")
    
    # Pompe
    print("\n💧 POMPE HYDRAULIQUE")
    print("-" * 60)
    pompe_gen = PompeGenerator(n_samples=500)
    df_pompe = pompe_gen.generate_with_faults()
    output_pompe = data_dir / "pompe.csv"
    df_pompe.to_csv(output_pompe, index=False, float_format='%.4f')
    print(f"✅ Créé: {output_pompe}")
    print(f"   Lignes: {len(df_pompe)}")
    print(f"   Colonnes: {', '.join(df_pompe.columns[1:])}")
    print(f"   Vibration: {df_pompe['vibration'].min():.3f} - {df_pompe['vibration'].max():.3f} g")
    print(f"   Pression in: {df_pompe['pressure_in'].min():.1f} - {df_pompe['pressure_in'].max():.1f} bar")
    print(f"   Pression out: {df_pompe['pressure_out'].min():.1f} - {df_pompe['pressure_out'].max():.1f} bar")
    print(f"   Débit: {df_pompe['flow_rate'].min():.1f} - {df_pompe['flow_rate'].max():.1f} L/min")
    
    # Compresseur
    print("\n🌀 COMPRESSEUR D'AIR")
    print("-" * 60)
    compresseur_gen = CompresseurGenerator(n_samples=500)
    df_compresseur = compresseur_gen.generate_with_faults()
    output_compresseur = data_dir / "compresseur.csv"
    df_compresseur.to_csv(output_compresseur, index=False, float_format='%.4f')
    print(f"✅ Créé: {output_compresseur}")
    print(f"   Lignes: {len(df_compresseur)}")
    print(f"   Colonnes: {', '.join(df_compresseur.columns[1:])}")
    print(f"   Pression: {df_compresseur['pressure'].min():.1f} - {df_compresseur['pressure'].max():.1f} bar")
    print(f"   Courant: {df_compresseur['current'].min():.1f} - {df_compresseur['current'].max():.1f} A")
    print(f"   Temp huile: {df_compresseur['temperature_oil'].min():.1f} - {df_compresseur['temperature_oil'].max():.1f} °C")
    print(f"   Temp air: {df_compresseur['temperature_air'].min():.1f} - {df_compresseur['temperature_air'].max():.1f} °C")
    
    # Échangeur
    print("\n🔥 ÉCHANGEUR THERMIQUE")
    print("-" * 60)
    echangeur_gen = EchangeurGenerator(n_samples=500)
    df_echangeur = echangeur_gen.generate_with_faults()
    output_echangeur = data_dir / "echangeur.csv"
    df_echangeur.to_csv(output_echangeur, index=False, float_format='%.4f')
    print(f"✅ Créé: {output_echangeur}")
    print(f"   Lignes: {len(df_echangeur)}")
    print(f"   Colonnes: {', '.join(df_echangeur.columns[1:])}")
    print(f"   Temp in hot: {df_echangeur['temp_in_hot'].min():.1f} - {df_echangeur['temp_in_hot'].max():.1f} °C")
    print(f"   Temp out hot: {df_echangeur['temp_out_hot'].min():.1f} - {df_echangeur['temp_out_hot'].max():.1f} °C")
    print(f"   Temp in cold: {df_echangeur['temp_in_cold'].min():.1f} - {df_echangeur['temp_in_cold'].max():.1f} °C")
    print(f"   Temp out cold: {df_echangeur['temp_out_cold'].min():.1f} - {df_echangeur['temp_out_cold'].max():.1f} °C")
    print(f"   Débit: {df_echangeur['flow_rate'].min():.1f} - {df_echangeur['flow_rate'].max():.1f} L/min")
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE")
    print("=" * 60)
    print(f"\n📁 Dossier: {data_dir}")
    print(f"📊 Fichiers créés: 4")
    print(f"📈 Lignes par fichier: 500")
    print(f"⏱️  Interval: 60 secondes (8h20 de données)")
    print("\n🔄 Défauts injectés:")
    print("   Moteur: Déséquilibre (70%) + Roulement (85%)")
    print("   Pompe: Cavitation (60%) + Usure joints (76%)")
    print("   Compresseur: Usure soupapes (64%) + Refroidissement (80%)")
    print("   Échangeur: Encrassement (56%) + Fuite (80%)")
    print("\n🚀 Pour utiliser:")
    print("   cd smartmaintain")
    print("   docker-compose restart iot ml")
    print("   # Attendre 20 secondes")
    print("   # Ouvrir http://localhost:3000\n")


if __name__ == '__main__':
    main()
