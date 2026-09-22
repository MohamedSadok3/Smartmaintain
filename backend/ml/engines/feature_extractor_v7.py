"""
Feature extraction utilities for V7 models.
Provides simple sensor input -> feature vector transformations.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any


# Constants
EPS = 1e-12
STAT_NAMES = ["min", "max", "mean", "std", "rms", "peak_to_peak", "crest", "slope", "q25", "q75"]

# Motor-specific constants
MOTOR_SAMPLING_RATE_HZ = 20_000
MOTOR_WINDOW_SIZE = 100_000
MOTOR_FEATURES = [
    "vibration_fft_mean", "vibration_fft_std", "vibration_fft_shape_factor",
    "vibration_fft_rms", "vibration_fft_impulse_factor",
    "vibration_fft_peak_to_peak", "vibration_fft_kurtosis",
    "vibration_fft_crest_factor", "vibration_fft_skewness",
]

# Pump constants
PUMP_SENSORS = ["vibration", "pressure", "temperature", "flow_rate"]

# Compressor constants
COMP_SENSORS = ["pressure", "temperature_oil", "current"]

# Heat exchanger constants
HX_RAW_SENSORS = ["temp_in_hot", "temp_out_hot", "temp_in_cold", "temp_out_cold", "flow_rate"]
HX_DERIVED_SENSORS = [
    "delta_hot", "delta_cold", "approach_hot", "approach_cold",
    "effectiveness_proxy", "heat_duty_hot", "heat_duty_cold", "energy_imbalance"
]
HX_SENSORS = HX_RAW_SENSORS + HX_DERIVED_SENSORS


def summarize(values: np.ndarray) -> np.ndarray:
    """
    Extract 10 statistical features from a time series.
    
    Args:
        values: 1D array of sensor values
        
    Returns:
        Array of 10 statistical features
    """
    x = np.asarray(values, dtype=np.float64)
    rms = float(np.sqrt(np.mean(x * x)))
    slope = float(np.polyfit(np.arange(len(x), dtype=float), x, 1)[0])
    
    result = [
        np.min(x),                                    # min
        np.max(x),                                    # max
        np.mean(x),                                   # mean
        np.std(x),                                    # std
        rms,                                          # rms
        np.ptp(x),                                    # peak_to_peak
        np.max(np.abs(x)) / max(rms, EPS),           # crest
        slope,                                        # slope
        np.quantile(x, 0.25),                        # q25
        np.quantile(x, 0.75),                        # q75
    ]
    
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def feature_names(sensors: List[str]) -> List[str]:
    """Generate feature names for given sensors."""
    return [f"{sensor}_{stat}" for sensor in sensors for stat in STAT_NAMES]


def extract_motor_features(vibration: np.ndarray) -> np.ndarray:
    """
    Extract 9 FFT features from motor vibration signal (VBL X-axis compatible).
    
    Args:
        vibration: 1D array of exactly 100,000 vibration samples (5s at 20kHz)
        
    Returns:
        Array of 9 FFT-based features
        
    Raises:
        ValueError: If input doesn't meet requirements
    """
    x = np.asarray(vibration, dtype=np.float64)
    
    # Validation
    if x.ndim != 1 or len(x) != MOTOR_WINDOW_SIZE:
        raise ValueError(
            f"Motor requires exactly {MOTOR_WINDOW_SIZE} vibration samples, got {x.shape}"
        )
    if not np.isfinite(x).all():
        raise ValueError("Motor vibration contains NaN or infinite values")
    
    # FFT computation
    dt = 1.0 / MOTOR_SAMPLING_RATE_HZ
    spectrum = np.abs(np.fft.rfft(x) * dt)[: 500 * 5]
    
    # Statistical features on spectrum
    mean_abs = float(np.mean(np.abs(spectrum)))
    rms_value = float(np.sqrt(np.mean(spectrum ** 2)))
    series = pd.Series(spectrum)
    
    features = np.asarray([
        np.mean(spectrum),                           # mean
        np.std(spectrum),                            # std
        rms_value / max(mean_abs, EPS),             # shape_factor
        rms_value,                                   # rms
        np.max(spectrum) / max(mean_abs, EPS),      # impulse_factor
        np.ptp(spectrum),                            # peak_to_peak
        series.kurt(),                               # kurtosis
        np.max(spectrum) / max(rms_value, EPS),     # crest_factor
        series.skew(),                               # skewness
    ], dtype=np.float64)
    
    if not np.isfinite(features).all():
        raise ValueError("Motor feature extraction produced non-finite values")
    
    return features


def extract_pump_features(data: Dict[str, List[float]]) -> np.ndarray:
    """
    Extract features from pump sensor data.
    
    Args:
        data: Dictionary with keys: vibration, pressure, temperature, flow_rate
              Each containing a list of at least 20 measurements
              
    Returns:
        Array of 40 features (10 stats × 4 sensors)
        
    Raises:
        ValueError: If required sensors are missing or data is insufficient
    """
    # Validate required sensors
    for sensor in PUMP_SENSORS:
        if sensor not in data:
            raise ValueError(f"Missing required pump sensor: {sensor}")
        if len(data[sensor]) < 20:
            raise ValueError(f"Pump sensor '{sensor}' requires at least 20 measurements, got {len(data[sensor])}")
    
    # Create DataFrame
    df = pd.DataFrame({sensor: data[sensor][:20] for sensor in PUMP_SENSORS})
    
    # Extract features for each sensor
    features = []
    for sensor in PUMP_SENSORS:
        sensor_features = summarize(df[sensor].values)
        features.extend(sensor_features)
    
    return np.array(features, dtype=np.float64)


def extract_compressor_features(data: Dict[str, List[float]]) -> np.ndarray:
    """
    Extract features from compressor sensor data.
    
    Args:
        data: Dictionary with keys: pressure, temperature_oil, current
              Each containing a list of at least 30 measurements
              
    Returns:
        Array of 30 features (10 stats × 3 sensors)
        
    Raises:
        ValueError: If required sensors are missing or data is insufficient
    """
    # Validate required sensors
    for sensor in COMP_SENSORS:
        if sensor not in data:
            raise ValueError(f"Missing required compressor sensor: {sensor}")
        if len(data[sensor]) < 30:
            raise ValueError(f"Compressor sensor '{sensor}' requires at least 30 measurements, got {len(data[sensor])}")
    
    # Create DataFrame
    df = pd.DataFrame({sensor: data[sensor][:30] for sensor in COMP_SENSORS})
    
    # Extract features for each sensor
    features = []
    for sensor in COMP_SENSORS:
        sensor_features = summarize(df[sensor].values)
        features.extend(sensor_features)
    
    return np.array(features, dtype=np.float64)


def extract_heat_exchanger_features(data: Dict[str, List[float]]) -> np.ndarray:
    """
    Extract features from heat exchanger sensor data.
    
    Args:
        data: Dictionary with keys: temp_in_hot, temp_out_hot, temp_in_cold, 
              temp_out_cold, flow_rate. Each containing at least 30 measurements.
              
    Returns:
        Array of 130 features (10 stats × 13 sensors including derived)
        
    Raises:
        ValueError: If required sensors are missing or data is insufficient
    """
    # Validate required sensors
    for sensor in HX_RAW_SENSORS:
        if sensor not in data:
            raise ValueError(f"Missing required heat exchanger sensor: {sensor}")
        if len(data[sensor]) < 30:
            raise ValueError(f"Heat exchanger sensor '{sensor}' requires at least 30 measurements, got {len(data[sensor])}")
    
    # Create DataFrame with raw sensors
    df = pd.DataFrame({sensor: data[sensor][:30] for sensor in HX_RAW_SENSORS})
    
    # Compute derived thermodynamic features
    df["delta_hot"] = df["temp_in_hot"] - df["temp_out_hot"]
    df["delta_cold"] = df["temp_out_cold"] - df["temp_in_cold"]
    df["approach_hot"] = df["temp_out_hot"] - df["temp_in_cold"]
    df["approach_cold"] = df["temp_in_hot"] - df["temp_out_cold"]
    df["effectiveness_proxy"] = df["delta_hot"] / np.maximum(
        df["temp_in_hot"] - df["temp_in_cold"], EPS
    )
    df["heat_duty_hot"] = df["flow_rate"] * df["delta_hot"]
    df["heat_duty_cold"] = df["flow_rate"] * df["delta_cold"]
    df["energy_imbalance"] = np.abs(
        df["heat_duty_hot"] - df["heat_duty_cold"]
    ) / np.maximum(np.abs(df["heat_duty_hot"]), EPS)
    
    # Extract features for all sensors (raw + derived)
    features = []
    for sensor in HX_SENSORS:
        sensor_features = summarize(df[sensor].values)
        features.extend(sensor_features)
    
    return np.array(features, dtype=np.float64)


class FeatureExtractorV7:
    """Unified feature extractor for V7 models."""
    
    # Equipment type mapping
    EQUIPMENT_EXTRACTORS = {
        "moteur": extract_motor_features,
        "pompe": extract_pump_features,
        "compresseur": extract_compressor_features,
        "echangeur": extract_heat_exchanger_features,
    }
    
    EQUIPMENT_FEATURE_NAMES = {
        "moteur": MOTOR_FEATURES,
        "pompe": feature_names(PUMP_SENSORS),
        "compresseur": feature_names(COMP_SENSORS),
        "echangeur": feature_names(HX_SENSORS),
    }
    
    @classmethod
    def extract(cls, equipment_type: str, sensor_data: Any) -> np.ndarray:
        """
        Extract features for a given equipment type.
        
        Args:
            equipment_type: One of 'moteur', 'pompe', 'compresseur', 'echangeur'
            sensor_data: Raw sensor data (format depends on equipment type)
                - moteur: 1D array of 100,000 vibration samples
                - pompe/compresseur/echangeur: Dict with sensor names and value lists
                
        Returns:
            Feature vector as numpy array
            
        Raises:
            ValueError: If equipment type is unknown or data is invalid
        """
        if equipment_type not in cls.EQUIPMENT_EXTRACTORS:
            raise ValueError(
                f"Unknown equipment type: {equipment_type}. "
                f"Valid types: {list(cls.EQUIPMENT_EXTRACTORS.keys())}"
            )
        
        extractor = cls.EQUIPMENT_EXTRACTORS[equipment_type]
        return extractor(sensor_data)
    
    @classmethod
    def get_feature_names(cls, equipment_type: str) -> List[str]:
        """Get feature names for a given equipment type."""
        if equipment_type not in cls.EQUIPMENT_FEATURE_NAMES:
            raise ValueError(f"Unknown equipment type: {equipment_type}")
        return cls.EQUIPMENT_FEATURE_NAMES[equipment_type]
    
    @classmethod
    def get_required_sensors(cls, equipment_type: str) -> List[str]:
        """Get required sensor names for a given equipment type."""
        sensor_map = {
            "moteur": ["vibration"],
            "pompe": PUMP_SENSORS,
            "compresseur": COMP_SENSORS,
            "echangeur": HX_RAW_SENSORS,
        }
        if equipment_type not in sensor_map:
            raise ValueError(f"Unknown equipment type: {equipment_type}")
        return sensor_map[equipment_type]
    
    @classmethod
    def get_window_size(cls, equipment_type: str) -> int:
        """Get required window size for a given equipment type."""
        window_sizes = {
            "moteur": 100_000,
            "pompe": 20,
            "compresseur": 30,
            "echangeur": 30,
        }
        if equipment_type not in window_sizes:
            raise ValueError(f"Unknown equipment type: {equipment_type}")
        return window_sizes[equipment_type]
