"""
SmartMaintain V7 Model Training Script
Generates model_bundle.joblib for each equipment type.

Strategy: Train synthetic data whose normal class is calibrated to the
actual CSV sensor ranges so the live CSV replay gets properly classified.
Faulty classes use clear deviations from those ranges.

Run inside the ml container:  python train_models.py
"""

import json
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("train")

MODELS_DIR = Path(__file__).resolve().parent / "models_v7"
DATA_DIR   = Path(__file__).resolve().parent.parent / "iot" / "data"
RNG = np.random.default_rng(42)
N_PER_CLASS = 4000
N_TEST      = 1000


# ---------------------------------------------------------------------------
# Statistical feature block (mirrors feature_extractor_v7.py → summarize())
# ---------------------------------------------------------------------------

def _stat_block(arr: np.ndarray) -> np.ndarray:
    """10 stats per sensor for a batch of shape (n, window)."""
    x   = arr.astype(np.float64)
    EPS = 1e-12
    rms   = np.sqrt(np.mean(x ** 2, axis=1))
    slope = np.polyfit(np.arange(x.shape[1], dtype=float), x.T, 1)[0]
    block = np.column_stack([
        np.min(x, axis=1),
        np.max(x, axis=1),
        np.mean(x, axis=1),
        np.std(x, axis=1),
        rms,
        np.ptp(x, axis=1),
        np.max(np.abs(x), axis=1) / np.maximum(rms, EPS),
        slope,
        np.quantile(x, 0.25, axis=1),
        np.quantile(x, 0.75, axis=1),
    ])
    return np.nan_to_num(block, nan=0.0, posinf=0.0, neginf=0.0)


def _infer_normal_stats(csv_path: Path, col: str, window: int = 20):
    """Read actual CSV to infer mean/std of a sensor column."""
    try:
        df = pd.read_csv(csv_path, usecols=[col])
        vals = df[col].dropna().values.astype(float)
        return float(np.mean(vals)), float(np.std(vals))
    except Exception as e:
        log.warning(f"Could not read {csv_path}/{col}: {e}")
        return None, None


# ---------------------------------------------------------------------------
# MOTOR  (9 pre-computed FFT features from VBL CSV vbl_feature_00..08)
# ---------------------------------------------------------------------------

def _load_motor_normal_ranges():
    """Read actual motor CSV to calibrate normal class."""
    path = DATA_DIR / "moteur.csv"
    try:
        df = pd.read_csv(path, usecols=[f"vbl_feature_{i:02d}" for i in range(9)])
        means = df.mean().values
        stds  = df.std().values
        log.info(f"Motor CSV calibration: means={np.round(means,4)}")
        return means, stds
    except Exception as e:
        log.warning(f"Could not read motor CSV: {e}. Using defaults.")
        return (np.array([0.008, 0.005, 1.02, 0.009, 2.8, 0.025, 2.5, 2.6, 0.15]),
                np.array([0.002, 0.001, 0.05, 0.002, 0.3, 0.005, 0.3, 0.3, 0.05]))


def make_motor_samples(label: str, n: int) -> np.ndarray:
    normal_means, normal_stds = _load_motor_normal_ranges()
    if label == "normal_operation":
        noise = RNG.normal(0, 1, (n, 9)) * normal_stds * 1.2
        return normal_means + noise
    elif label == "degradation_roulement":
        # Bearing fault: higher kurtosis (idx 6), higher crest (idx 7), higher peak-to-peak (idx 5)
        fault = normal_means.copy()
        fault[5] *= 4.0   # peak_to_peak
        fault[6] *= 5.0   # kurtosis
        fault[7] *= 3.5   # crest_factor
        noise = RNG.normal(0, 1, (n, 9)) * normal_stds * 2.0
        return fault + noise
    else:  # desequilibre_desalignement
        fault = normal_means.copy()
        fault[0] *= 3.5   # mean amplitude higher
        fault[3] *= 3.5   # rms higher
        fault[4] *= 4.0   # impulse_factor
        noise = RNG.normal(0, 1, (n, 9)) * normal_stds * 2.0
        return fault + noise


# ---------------------------------------------------------------------------
# PUMP  (4 sensors × 20 readings)
# CSV columns: Accelerometer1RMS, Pressure, Temperature, Volume Flow RateRMS
# ---------------------------------------------------------------------------

def make_pump_samples(label: str, n: int) -> np.ndarray:
    path = DATA_DIR / "pompe.csv"
    # Read actual normal stats from CSV
    vib_m,  vib_s  = _infer_normal_stats(path, "Accelerometer1RMS")  or (0.25, 0.015)
    pres_m, pres_s = _infer_normal_stats(path, "Pressure")           or (5.0,  0.20)
    temp_m, temp_s = _infer_normal_stats(path, "Temperature")        or (45.0, 1.0)
    flow_m, flow_s = _infer_normal_stats(path, "Volume Flow RateRMS")or (100.0, 3.0)

    if label == "normal_operation":
        vib  = RNG.normal(vib_m,  vib_s  * 1.2, (n, 20))
        pres = RNG.normal(pres_m, pres_s * 1.2, (n, 20))
        temp = RNG.normal(temp_m, temp_s * 1.2, (n, 20))
        flow = RNG.normal(flow_m, flow_s * 1.2, (n, 20))
    elif label == "cavitation":
        vib  = RNG.normal(vib_m  * 2.5, vib_s  * 3.0, (n, 20))  # vibration spikes
        pres = RNG.normal(pres_m * 0.5, pres_s * 3.0, (n, 20))  # pressure unstable/low
        temp = RNG.normal(temp_m * 1.1, temp_s * 2.0, (n, 20))
        flow = RNG.normal(flow_m * 0.75,flow_s * 3.0, (n, 20))  # reduced flow
    else:  # fuite_joints
        vib  = RNG.normal(vib_m  * 1.5, vib_s  * 2.0, (n, 20))
        pres = RNG.normal(pres_m * 0.8, pres_s * 2.0, (n, 20))  # slight pressure loss
        temp = RNG.normal(temp_m * 1.2, temp_s * 2.0, (n, 20))  # warmer
        flow = RNG.normal(flow_m * 0.85,flow_s * 2.0, (n, 20))

    return np.hstack([_stat_block(vib), _stat_block(pres),
                      _stat_block(temp), _stat_block(flow)])


# ---------------------------------------------------------------------------
# COMPRESSOR  (3 sensors × 30 readings)
# CSV columns: pressure, temperature_oil, current
# ---------------------------------------------------------------------------

def make_compressor_samples(label: str, n: int) -> np.ndarray:
    path = DATA_DIR / "compresseur.csv"
    pres_m, pres_s = _infer_normal_stats(path, "pressure")         or (7.8,  0.12)
    temp_m, temp_s = _infer_normal_stats(path, "temperature_oil")  or (68.0, 1.5)
    curr_m, curr_s = _infer_normal_stats(path, "current")          or (17.0, 0.6)

    if label == "normal_operation":
        pres = RNG.normal(pres_m, pres_s * 1.2, (n, 30))
        temp = RNG.normal(temp_m, temp_s * 1.2, (n, 30))
        curr = RNG.normal(curr_m, curr_s * 1.2, (n, 30))
    elif label == "fuite_air":
        pres = RNG.normal(pres_m * 0.72, pres_s * 4.0, (n, 30))  # pressure drops
        temp = RNG.normal(temp_m * 1.12, temp_s * 2.5, (n, 30))
        curr = RNG.normal(curr_m * 1.20, curr_s * 2.5, (n, 30))  # motor compensates
    else:  # surchauffe
        pres = RNG.normal(pres_m * 1.06, pres_s * 2.0, (n, 30))
        temp = RNG.normal(temp_m * 1.40, temp_s * 3.5, (n, 30))  # high temperature
        curr = RNG.normal(curr_m * 1.35, curr_s * 3.0, (n, 30))

    return np.hstack([_stat_block(pres), _stat_block(temp), _stat_block(curr)])


# ---------------------------------------------------------------------------
# HEAT EXCHANGER  (5 raw + 8 derived sensors × 30 readings)
# CSV columns: temp_in_hot, temp_out_hot, temp_in_cold, temp_out_cold, flow_rate
# ---------------------------------------------------------------------------

def make_hx_samples(label: str, n: int) -> np.ndarray:
    path = DATA_DIR / "echangeur.csv"
    tih_m, tih_s = _infer_normal_stats(path, "temp_in_hot")   or (80.0, 2.0)
    toh_m, toh_s = _infer_normal_stats(path, "temp_out_hot")  or (45.0, 1.5)
    tic_m, tic_s = _infer_normal_stats(path, "temp_in_cold")  or (15.0, 1.0)
    toc_m, toc_s = _infer_normal_stats(path, "temp_out_cold") or (36.0, 1.5)
    fr_m,  fr_s  = _infer_normal_stats(path, "flow_rate")     or (100.0, 4.0)

    if label == "normal_operation":
        tih = RNG.normal(tih_m, tih_s * 1.2, (n, 30))
        toh = RNG.normal(toh_m, toh_s * 1.2, (n, 30))
        tic = RNG.normal(tic_m, tic_s * 1.2, (n, 30))
        toc = RNG.normal(toc_m, toc_s * 1.2, (n, 30))
        fr  = RNG.normal(fr_m,  fr_s  * 1.2, (n, 30))
    elif label == "encrassement":
        tih = RNG.normal(tih_m * 1.07, tih_s * 1.5, (n, 30))
        toh = RNG.normal(toh_m * 1.25, toh_s * 1.5, (n, 30))  # hot outlet hotter
        tic = RNG.normal(tic_m,         tic_s * 1.2, (n, 30))
        toc = RNG.normal(toc_m * 0.80, toc_s * 1.5, (n, 30))  # cold outlet cooler
        fr  = RNG.normal(fr_m  * 0.90, fr_s  * 1.5, (n, 30))
    else:  # fuite_thermique
        tih = RNG.normal(tih_m * 0.94, tih_s * 1.5, (n, 30))
        toh = RNG.normal(toh_m * 0.93, toh_s * 2.0, (n, 30))
        tic = RNG.normal(tic_m * 1.30, tic_s * 2.0, (n, 30))  # cold side warms up
        toc = RNG.normal(toc_m * 1.10, toc_s * 2.0, (n, 30))
        fr  = RNG.normal(fr_m  * 0.95, fr_s  * 2.0, (n, 30))

    EPS = 1e-12
    dh  = tih - toh
    dc  = toc - tic
    ah  = toh - tic
    ac  = tih - toc
    eff = dh / np.maximum(tih - tic, EPS)
    hdh = fr * dh
    hdc = fr * dc
    ei  = np.abs(hdh - hdc) / np.maximum(np.abs(hdh), EPS)

    return np.hstack([
        _stat_block(tih), _stat_block(toh), _stat_block(tic),
        _stat_block(toc), _stat_block(fr),
        _stat_block(dh),  _stat_block(dc),  _stat_block(ah),
        _stat_block(ac),  _stat_block(eff), _stat_block(hdh),
        _stat_block(hdc), _stat_block(ei),
    ])


# ---------------------------------------------------------------------------
# Per-equipment config
# ---------------------------------------------------------------------------

EQUIPMENTS = {
    "moteur": {
        "classes": ["normal_operation", "degradation_roulement", "desequilibre_desalignement"],
        "feature_names": [
            "vibration_fft_mean", "vibration_fft_std", "vibration_fft_shape_factor",
            "vibration_fft_rms", "vibration_fft_impulse_factor",
            "vibration_fft_peak_to_peak", "vibration_fft_kurtosis",
            "vibration_fft_crest_factor", "vibration_fft_skewness",
        ],
        "raw_sensor_names": ["vibration"],
        "window_size": 100_000,
        "sampling_rate_hz": 20_000,
        "make_fn": make_motor_samples,
    },
    "pompe": {
        "classes": ["normal_operation", "cavitation", "fuite_joints"],
        "feature_names": [f"{s}_{st}" for s in ["vibration","pressure","temperature","flow_rate"]
                          for st in ["min","max","mean","std","rms","peak_to_peak","crest","slope","q25","q75"]],
        "raw_sensor_names": ["vibration", "pressure", "temperature", "flow_rate"],
        "window_size": 20,
        "sampling_rate_hz": None,
        "make_fn": make_pump_samples,
    },
    "compresseur": {
        "classes": ["normal_operation", "fuite_air", "surchauffe"],
        "feature_names": [f"{s}_{st}" for s in ["pressure","temperature_oil","current"]
                          for st in ["min","max","mean","std","rms","peak_to_peak","crest","slope","q25","q75"]],
        "raw_sensor_names": ["pressure", "temperature_oil", "current"],
        "window_size": 30,
        "sampling_rate_hz": None,
        "make_fn": make_compressor_samples,
    },
    "echangeur": {
        "classes": ["normal_operation", "encrassement", "fuite_thermique"],
        "feature_names": [f"{s}_{st}"
                          for s in ["temp_in_hot","temp_out_hot","temp_in_cold","temp_out_cold","flow_rate",
                                    "delta_hot","delta_cold","approach_hot","approach_cold",
                                    "effectiveness_proxy","heat_duty_hot","heat_duty_cold","energy_imbalance"]
                          for st in ["min","max","mean","std","rms","peak_to_peak","crest","slope","q25","q75"]],
        "raw_sensor_names": ["temp_in_hot","temp_out_hot","temp_in_cold","temp_out_cold","flow_rate"],
        "window_size": 30,
        "sampling_rate_hz": None,
        "make_fn": make_hx_samples,
    },
}


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train_one(name: str, cfg: dict):
    log.info(f"=== Training {name} ===")
    folder = MODELS_DIR / name
    metadata = json.loads((folder / "metadata.json").read_text())

    classes = cfg["classes"]
    make_fn = cfg["make_fn"]

    X_list, y_list = [], []
    for label in classes:
        X_list.append(make_fn(label, N_PER_CLASS + N_TEST))
        y_list.extend([label] * (N_PER_CLASS + N_TEST))

    X = np.vstack(X_list)
    y = np.array(y_list)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=N_TEST * len(classes), random_state=42, stratify=y
    )

    log.info(f"  Train: {X_train.shape}, Test: {X_test.shape}")

    model = ExtraTreesClassifier(
        n_estimators=200, max_depth=None,
        min_samples_split=2, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    log.info(f"  Accuracy: {acc:.4f}")

    bundle = {
        "model":           model,
        "classes":         classes,
        "feature_names":   cfg["feature_names"],
        "machine":         name,
        "source_manifest": metadata["source_manifest"],
        "raw_sensor_names": cfg["raw_sensor_names"],
        "window_size":     cfg["window_size"],
        "sampling_rate_hz": cfg["sampling_rate_hz"],
        "feature_extractor_version": "smartmaintain-statistics-v1",
        "version":         metadata["version"],
    }

    bundle_path = folder / "model_bundle.joblib"
    joblib.dump(bundle, bundle_path, compress=3)
    log.info(f"  Saved → {bundle_path}")

    metrics = json.loads((folder / "metrics.json").read_text())
    metrics["accuracy"] = acc
    metrics["classification_report"] = report
    metrics["selected_model"] = "extra_trees"
    (folder / "metrics.json").write_text(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    for eq_name, eq_cfg in EQUIPMENTS.items():
        train_one(eq_name, eq_cfg)
    log.info("All models trained and calibrated to CSV ranges.")
