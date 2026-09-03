"""
ReplayService — IoT Service for V7 Models
==========================================
Reads CSV sensor data and publishes V7-compatible raw sensor arrays to Redis.

Features:
- Motor: Pre-computed VBL features (9 FFT features)
- Pump: 4 sensors × 20 measurements
- Compressor: 3 sensors × 30 measurements
- Heat Exchanger: 5 sensors × 30 measurements
"""

import json
import logging
import threading
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import redis

from shared.config import get_env
from shared.constants import MACHINE_TYPES, REDIS_DEFAULT_URL, REDIS_SENSOR_CHANNEL
from shared.ml_config import WINDOW_SIZES

logger = logging.getLogger(__name__)


class ReplayService:
    """Replay CSV sensor data in V7 format."""
    
    # Sensor mappings: V7 sensor name → CSV column name
    SENSOR_MAPPINGS = {
        "pompe": {
            "vibration": "Accelerometer1RMS",
            "pressure": "Pressure",
            "temperature": "Temperature",
            "flow_rate": "Volume Flow RateRMS"
        },
        "compresseur": {
            "pressure": "pressure",
            "temperature_oil": "temperature_oil",
            "current": "current"
        },
        "echangeur": {
            "temp_in_hot": "temp_in_hot",
            "temp_out_hot": "temp_out_hot",
            "temp_in_cold": "temp_in_cold",
            "temp_out_cold": "temp_out_cold",
            "flow_rate": "flow_rate"
        }
    }

    def __init__(self):
        """Initialize ReplayService."""
        redis_url = get_env("REDIS_URL", REDIS_DEFAULT_URL)
        self.redis_pool = redis.ConnectionPool.from_url(
            redis_url, max_connections=10, decode_responses=True
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        self.channel_name = get_env("IOT_CHANNEL", REDIS_SENSOR_CHANNEL)
        self.data_dir = Path(__file__).parent.parent / "data"
        self.replay_interval_seconds = int(get_env("IOT_REPLAY_INTERVAL_SECONDS", 2))
        
        plant_id_env = get_env("IOT_PLANT_ID")
        self.plant_id = int(plant_id_env) if plant_id_env else None
        
        # Normal bias mode: 80% of data will be "normalized" to typical ranges
        self.normal_bias_ratio = float(get_env("IOT_NORMAL_BIAS", "0.8"))
        
        self.buffers = {
            machine: deque(maxlen=window_size)
            for machine, window_size in WINDOW_SIZES.items()
        }
        
        logger.info(
            f"ReplayService initialized: interval={self.replay_interval_seconds}s, normal_bias={self.normal_bias_ratio}"
        )

    def _normalize_to_normal_range(self, machine: str, sensor_name: str, value: float) -> float:
        """
        Adjust sensor values to typical normal operation ranges.
        This reduces alert frequency for demo purposes.
        
        Args:
            machine: Equipment type
            sensor_name: Sensor name
            value: Original sensor value
            
        Returns:
            Normalized value within normal range
        """
        import random
        
        # Define typical "normal" ranges per equipment/sensor
        normal_ranges = {
            "pompe": {
                "vibration": (0.2, 0.4),  # Low vibration
                "pressure": (4.8, 5.2),   # Stable pressure around 5 bar
                "temperature": (40, 50),  # Moderate temp
                "flow_rate": (95, 105)    # Steady flow around 100
            },
            "compresseur": {
                "pressure": (6.5, 7.5),   # Stable pressure ~7 bar
                "temperature_oil": (60, 75),  # Normal oil temp
                "current": (8.5, 10.5)    # Steady current ~9-10 A
            },
            "echangeur": {
                "temp_in_hot": (80, 90),   # Hot inlet stable
                "temp_out_hot": (55, 65),  # Hot outlet
                "temp_in_cold": (15, 20),  # Cold inlet
                "temp_out_cold": (35, 42), # Cold outlet
                "flow_rate": (0.8, 1.2)    # Steady flow
            }
        }
        
        if machine not in normal_ranges:
            return value
        
        sensor_ranges = normal_ranges[machine]
        if sensor_name not in sensor_ranges:
            return value
        
        min_val, max_val = sensor_ranges[sensor_name]
        
        # Return value within normal range with small variation
        return random.uniform(min_val, max_val)

    def _should_normalize(self) -> bool:
        """Determine if current reading should be normalized based on bias ratio."""
        import random
        return random.random() < self.normal_bias_ratio


    def publish_machine_window(self, machine: str, window: List[Dict]) -> Optional[Dict]:
        """
        Publish V7-compatible sensor data to Redis.
        
        Args:
            machine: Equipment type
            window: Sliding window of sensor readings
            
        Returns:
            Published payload or None
        """
        try:
            if not window:
                return None
                
            required_size = WINDOW_SIZES.get(machine)
            if not required_size or len(window) != required_size:
                return None
            
            timestamp = window[-1].get("timestamp")
            sensor_map = self.SENSOR_MAPPINGS.get(machine, {})
            
            if not sensor_map:
                logger.warning(f"No V7 mapping for machine '{machine}'")
                return None
            
            # Build V7 sensors: {v7_name: [values...]}
            v7_sensors = {}
            display_sensors = {}
            
            # Check if we should normalize this batch
            normalize = self._should_normalize()
            
            for v7_name, csv_column in sensor_map.items():
                try:
                    values = [float(row[csv_column]) for row in window]
                    
                    # Apply normalization if enabled
                    if normalize:
                        values = [self._normalize_to_normal_range(machine, v7_name, v) for v in values]
                    
                    v7_sensors[v7_name] = values
                    display_sensors[v7_name] = values[-1]
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to map '{v7_name}' from '{csv_column}': {e}")
                    continue
            
            if not v7_sensors:
                return None
            
            payload = {
                "machine": machine,
                "sensors": v7_sensors,  # V7 format: direct sensor arrays
                "display_sensors": display_sensors,
                "timestamp": timestamp,
                "source_type": "csv_simulation_v7",
                "model_version": "v7"
            }
            
            if self.plant_id is not None:
                payload["plant_id"] = self.plant_id
            
            self.redis_client.publish(self.channel_name, json.dumps(payload))
            logger.debug(f"Published V7 data for {machine}: {list(v7_sensors.keys())}")
            
            return payload
            
        except Exception as e:
            logger.error(f"Failed to publish V7 data for '{machine}': {e}", exc_info=True)
            return None

    def publish_motor_features(self, row: Dict) -> Optional[Dict]:
        """
        Publish motor pre-computed VBL features to Redis.
        Motor V7 model expects 9 FFT features with specific names.
        
        Args:
            row: CSV row with vbl_feature_00 to vbl_feature_26
            
        Returns:
            Published payload or None
        """
        try:
            # V7 motor expects these 9 FFT feature names
            v7_motor_features = [
                "vibration_fft_mean",
                "vibration_fft_std", 
                "vibration_fft_shape_factor",
                "vibration_fft_rms",
                "vibration_fft_impulse_factor",
                "vibration_fft_peak_to_peak",
                "vibration_fft_kurtosis",
                "vibration_fft_crest_factor",
                "vibration_fft_skewness",
            ]
            
            # Map first 9 VBL features to V7 motor FFT feature names
            features = {}
            display_sensors = {}
            
            import random
            
            # Check if we should apply normal bias
            normalize = self._should_normalize()
            
            for i, v7_name in enumerate(v7_motor_features):
                vbl_name = f"vbl_feature_{i:02d}"
                if vbl_name not in row:
                    logger.warning(f"Missing motor feature: {vbl_name}")
                    return None
                
                base_value = float(row[vbl_name])
                
                if normalize:
                    # Normal mode: add very small variation (±2%) for stable operation
                    variation = base_value * random.uniform(-0.02, 0.02)
                else:
                    # Faulty mode: add larger variation (±10%) for alert generation
                    variation = base_value * random.uniform(-0.1, 0.1)
                    
                features[v7_name] = base_value + variation
            
            # For display: use features with different magnitudes for better visualization
            # Feature 0 (mean): ~0.0, Feature 5 (peak_to_peak): ~0.05, Feature 8 (skewness): ~0.08
            display_features = [
                ("vibration_fft_mean", features["vibration_fft_mean"]),
                ("vibration_fft_peak_to_peak", features["vibration_fft_peak_to_peak"]),
                ("vibration_fft_skewness", features["vibration_fft_skewness"]),
            ]
            for name, value in display_features:
                display_sensors[name] = value
            
            payload = {
                "machine": "moteur",
                "sensors": {"features": features},  # V7 motor format: pre-computed features
                "display_sensors": display_sensors,
                "timestamp": row.get("timestamp"),
                "source_type": "csv_simulation_v7",
                "model_version": "v7"
            }
            
            if self.plant_id is not None:
                payload["plant_id"] = self.plant_id
            
            self.redis_client.publish(self.channel_name, json.dumps(payload))
            logger.debug(f"Published V7 motor features: 9 FFT features")
            
            return payload
            
        except Exception as e:
            logger.error(f"Failed to publish motor features: {e}", exc_info=True)
            return None

    def replay_csv(self, machine: str):
        """
        Read CSV and replay as V7-compatible data.
        
        Args:
            machine: Equipment type
        """
        path = self.data_dir / f"{machine}.csv"
        
        if not path.exists():
            logger.error(f"CSV not found: {path}")
            return
        
        try:
            logger.info(f"Loading CSV for '{machine}': {path}")
            df = pd.read_csv(path)
            rows = df.to_dict(orient="records")
            logger.info(f"Loaded {len(rows)} rows for '{machine}'")
            
            # Special handling for motor (features-only mode)
            if machine == "moteur":
                logger.info(f"Motor uses feature-only mode (27 VBL features)")
                while True:
                    for row in rows:
                        self.publish_motor_features(row)
                        time.sleep(self.replay_interval_seconds)
                return
            
            required_size = WINDOW_SIZES.get(machine)
            if not required_size:
                logger.info(f"No window size defined for '{machine}'")
                return
            
            if len(rows) < required_size:
                logger.warning(
                    f"CSV for '{machine}' has {len(rows)} rows, less than window {required_size}"
                )
            
            window = deque(maxlen=required_size)
            
            # Infinite loop: continuous replay
            while True:
                for row in rows:
                    window.append(row)
                    
                    if len(window) == required_size:
                        self.publish_machine_window(machine, list(window))
                    
                    time.sleep(self.replay_interval_seconds)
                    
        except Exception as e:
            logger.error(f"Replay failed for '{machine}': {e}", exc_info=True)

    def _run_replay_with_retries(self, machine: str):
        """Keep replay alive with retries."""
        while True:
            try:
                self.replay_csv(machine)
            except Exception as e:
                logger.error(f"Replay error for '{machine}': {e}")
            logger.info(f"Retrying replay for '{machine}' in 10 seconds")
            time.sleep(10)

    def start_replay_threads(self):
        """Start replay threads for all machines."""
        logger.info(f"Starting replay threads for: {MACHINE_TYPES}")
        
        threads = []
        for machine in MACHINE_TYPES:
            thread = threading.Thread(
                target=self._run_replay_with_retries,
                args=(machine,),
                daemon=True,
                name=f"Replay-{machine}"
            )
            thread.start()
            threads.append(thread)
            logger.info(f"Started replay thread for '{machine}'")
        
        return threads
