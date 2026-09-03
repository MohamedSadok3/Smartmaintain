"""Model loader and prediction service for V7 models with simple input contracts."""

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

import joblib
import numpy as np

# Add parent directory to path for shared imports
PARENT_DIR = Path(__file__).resolve().parents[1]
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from engines.feature_extractor_v7 import FeatureExtractorV7

logger = logging.getLogger(__name__)

EQUIPMENTS = ("moteur", "pompe", "compresseur", "echangeur")
REQUIRED_BUNDLE_KEYS = {"model", "classes", "feature_names", "machine", "source_manifest"}


# ============================================================================
# Exception Classes
# ============================================================================

class ModelServiceError(Exception):
    """Base exception for model service errors."""
    code, status_code = "prediction_error", 422

    def __init__(self, message: str, **details: Any):
        super().__init__(message)
        self.message, self.details = message, details

    def to_dict(self):
        return {"error": self.code, "message": self.message, **self.details}


class UnknownEquipmentError(ModelServiceError):
    """Raised when equipment type is not recognized."""
    code = "unknown_equipment"


class MissingFeaturesError(ModelServiceError):
    """Raised when required features are missing."""
    code = "missing_features"


class InvalidFeatureValueError(ModelServiceError):
    """Raised when feature value is invalid (NaN, inf, wrong type)."""
    code = "invalid_feature_value"


class InsufficientAcquisitionError(ModelServiceError):
    """Raised when not enough sensor data points are provided."""
    code, status_code = "acquisition_insuffisante", 202


class InvalidBundleError(ModelServiceError):
    """Raised when model bundle is invalid or incomplete."""
    code, status_code = "invalid_model_bundle", 503


class InvalidSeriesLengthError(ModelServiceError):
    """Raised when sensor series has wrong length."""
    code = "invalid_series_length"


class UnsupportedRawInputError(ModelServiceError):
    """Raised when raw input is not supported for this model."""
    code = "unsupported_raw_input"


class ModelInputNotAvailableError(ModelServiceError):
    """Raised when model input type is not available."""
    code = "model_input_not_available"


# ============================================================================
# Model Bundle
# ============================================================================

@dataclass(frozen=True)
class LoadedBundle:
    """Represents a loaded V7 model bundle."""
    machine: str
    model: Any
    classes: Tuple[str, ...]
    feature_names: Tuple[str, ...]
    source_manifest: Dict
    metadata: Dict
    metrics: Dict
    raw_sensor_names: Tuple[str, ...]
    window_size: int
    sampling_rate_hz: Optional[int]
    feature_extractor_version: str
    estimator_type: str
    version: str


# ============================================================================
# Model Service
# ============================================================================

class ModelService:
    """
    Load and manage V7 model bundles with simple input contracts.
    
    V7 models accept raw sensor data instead of pre-computed features:
    - moteur: Pre-computed VBL features (9 FFT features)
    - pompe: 4 sensors × 20 measurements
    - compresseur: 3 sensors × 30 measurements
    - echangeur: 5 sensors × 30 measurements
    """

    def __init__(self, models_dir: Optional[str] = None, recommendations_path: Optional[str] = None):
        """
        Initialize V7 model service.
        
        Args:
            models_dir: Path to models_v7 directory
            recommendations_path: Path to recommendations.json
        """
        self.model_version = "v7"
        
        # Set default paths
        default_models = Path(__file__).resolve().parents[1] / "models_v7"
        self.models_dir = Path(models_dir or default_models).resolve()
        
        default_recommendations = Path(__file__).resolve().parents[1] / "config" / "recommendations.json"
        recommendations_path = recommendations_path or default_recommendations
        
        # Load manifest
        manifest_path = self.models_dir / "manifest.json"
        if not manifest_path.exists():
            raise InvalidBundleError(f"Manifest not found: {manifest_path}")
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        
        # Load recommendations
        self.recommendations = self._load_recommendations(recommendations_path)
        
        # Load all model bundles
        self.bundles = {name: self._load(name) for name in EQUIPMENTS}
        
        logger.info(f"ModelService initialized with {len(self.bundles)} models from {self.models_dir}")

    @staticmethod
    def _load_recommendations(path: Path) -> Dict:
        """Load and validate recommendations file."""
        if not Path(path).exists():
            logger.warning(f"Recommendations file not found: {path}, using empty recommendations")
            return {}
        
        recommendations = json.loads(Path(path).read_text(encoding="utf-8"))
        expected = {
            "degradation_roulement", "desequilibre_desalignement", "cavitation", "fuite_joints",
            "fuite_air", "surchauffe", "encrassement", "fuite_thermique",
        }
        
        if set(recommendations) != expected:
            logger.warning("Recommendations file doesn't cover all 8 defects")
        
        return recommendations

    def _load(self, machine: str) -> LoadedBundle:
        """
        Load a single model bundle.
        
        Args:
            machine: Equipment type (moteur, pompe, compresseur, echangeur)
            
        Returns:
            LoadedBundle instance
            
        Raises:
            InvalidBundleError: If bundle is invalid or incomplete
        """
        folder = self.models_dir / machine
        bundle_path = folder / "model_bundle.joblib"
        metadata_path = folder / "metadata.json"
        metrics_path = folder / "metrics.json"
        
        # Check required files
        if not bundle_path.is_file():
            raise InvalidBundleError(f"Model bundle not found: {bundle_path}", equipment_type=machine)
        if not metadata_path.is_file():
            raise InvalidBundleError(f"Metadata not found: {metadata_path}", equipment_type=machine)
        if not metrics_path.is_file():
            raise InvalidBundleError(f"Metrics not found: {metrics_path}", equipment_type=machine)
        
        # Load bundle
        bundle = joblib.load(bundle_path)
        if not isinstance(bundle, dict):
            raise InvalidBundleError("Bundle must be a dictionary", equipment_type=machine)
        
        # Validate required keys
        missing = sorted(REQUIRED_BUNDLE_KEYS - set(bundle))
        if missing:
            raise InvalidBundleError("Incomplete bundle", equipment_type=machine, missing=missing)
        
        # Validate machine name
        if bundle["machine"] != machine:
            raise InvalidBundleError(
                f"Machine mismatch: bundle={bundle['machine']}, folder={machine}",
                equipment_type=machine
            )
        
        # Load and validate model
        model = bundle["model"]
        
        # Set single-row prediction mode (no parallel processing needed)
        if hasattr(model, "n_jobs"):
            model.n_jobs = 1
        
        # Validate model interface
        if not callable(getattr(model, "predict", None)):
            raise InvalidBundleError("Model must have predict() method", equipment_type=machine)
        if not callable(getattr(model, "predict_proba", None)):
            raise InvalidBundleError("Model must have predict_proba() method", equipment_type=machine)
        
        # Extract and validate classes
        classes = tuple(str(v) for v in bundle["classes"])
        if not classes or len(set(classes)) != len(classes):
            raise InvalidBundleError("Invalid classes", equipment_type=machine)
        
        # Extract and validate feature names
        feature_names = tuple(str(v) for v in bundle["feature_names"])
        if not feature_names or len(set(feature_names)) != len(feature_names):
            raise InvalidBundleError("Invalid feature_names", equipment_type=machine)
        
        # Validate feature count
        n_features = int(getattr(model, "n_features_in_", len(feature_names)))
        if n_features != len(feature_names):
            raise InvalidBundleError(
                f"Feature count mismatch: model={n_features}, bundle={len(feature_names)}",
                equipment_type=machine
            )
        
        # Load metadata and metrics
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        
        # Validate consistency
        for key in ("machine", "classes", "feature_names", "source_manifest"):
            if bundle[key] != metadata.get(key):
                raise InvalidBundleError(
                    f"Bundle and metadata inconsistent for '{key}'",
                    equipment_type=machine
                )
        
        # Extract V7-specific fields
        raw_sensor_names = bundle.get("raw_sensor_names")
        if not raw_sensor_names:
            raise InvalidBundleError("V7 bundles must specify raw_sensor_names", equipment_type=machine)
        
        window_size = bundle.get("window_size")
        if window_size is None:
            raise InvalidBundleError("V7 bundles must specify window_size", equipment_type=machine)
        
        sampling_rate = bundle.get("sampling_rate_hz")
        feature_extractor_version = bundle.get("feature_extractor_version", "unknown")
        
        return LoadedBundle(
            machine=machine,
            model=model,
            classes=classes,
            feature_names=feature_names,
            source_manifest=dict(bundle["source_manifest"]),
            metadata=metadata,
            metrics=metrics,
            raw_sensor_names=tuple(raw_sensor_names),
            window_size=int(window_size),
            sampling_rate_hz=int(sampling_rate) if sampling_rate is not None else None,
            feature_extractor_version=feature_extractor_version,
            estimator_type=type(model).__name__,
            version=bundle.get("version", metadata.get("version", "unknown")),
        )

    def get_bundle(self, machine: str) -> LoadedBundle:
        """
        Get a loaded model bundle.
        
        Args:
            machine: Equipment type
            
        Returns:
            LoadedBundle instance
            
        Raises:
            UnknownEquipmentError: If machine type is not supported
        """
        name = str(machine or "").strip().lower()
        if name not in self.bundles:
            raise UnknownEquipmentError(
                "Unknown equipment type",
                equipment_type=machine,
                supported=list(EQUIPMENTS)
            )
        return self.bundles[name]

    @staticmethod
    def _validate_number(value: Any, name: str) -> float:
        """Validate and convert a value to a finite float."""
        if isinstance(value, bool):
            raise InvalidFeatureValueError("Boolean not allowed", feature=name)
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidFeatureValueError("Non-numeric value", feature=name) from exc
        if not math.isfinite(value):
            raise InvalidFeatureValueError("NaN or infinite value not allowed", feature=name)
        return value

    def _validate_sensor_data(self, machine: str, sensor_data: Dict) -> Dict:
        """
        Validate raw sensor data for a given machine.
        
        Args:
            machine: Equipment type
            sensor_data: Dictionary with sensor names and value arrays
            
        Returns:
            Validated sensor data
            
        Raises:
            InvalidFeatureValueError: If data is invalid
            InsufficientAcquisitionError: If not enough data points
            InvalidSeriesLengthError: If too many data points
        """
        bundle = self.get_bundle(machine)
        
        # Check required sensors
        missing_sensors = set(bundle.raw_sensor_names) - set(sensor_data.keys())
        if missing_sensors:
            raise InvalidFeatureValueError(
                f"Missing required sensors: {sorted(missing_sensors)}",
                equipment_type=machine,
                required_sensors=list(bundle.raw_sensor_names)
            )
        
        # Validate data format
        if machine == "moteur":
            # Motor expects a single vibration array
            vibration = sensor_data.get("vibration")
            if not isinstance(vibration, (list, tuple, np.ndarray)):
                raise InvalidFeatureValueError(
                    "Motor vibration must be an array",
                    equipment_type=machine
                )
            
            vibration = np.asarray(vibration, dtype=np.float64)
            
            if len(vibration) < bundle.window_size:
                raise InsufficientAcquisitionError(
                    f"Insufficient vibration samples: got {len(vibration)}, need {bundle.window_size}",
                    equipment_type=machine,
                    received=len(vibration),
                    required=bundle.window_size,
                    status="acquisition_continue"
                )
            
            if len(vibration) > bundle.window_size:
                raise InvalidSeriesLengthError(
                    f"Too many vibration samples: got {len(vibration)}, expected exactly {bundle.window_size}",
                    equipment_type=machine,
                    received=len(vibration),
                    required=bundle.window_size
                )
            
            return {"vibration": vibration}
        
        else:
            # Other equipment: validate all sensors have same length
            lengths = {}
            validated = {}
            
            for sensor in bundle.raw_sensor_names:
                values = sensor_data[sensor]
                if not isinstance(values, (list, tuple)):
                    raise InvalidFeatureValueError(
                        f"Sensor '{sensor}' must be an array",
                        equipment_type=machine,
                        sensor=sensor
                    )
                
                # Validate each value
                validated_values = [self._validate_number(v, sensor) for v in values]
                lengths[sensor] = len(validated_values)
                validated[sensor] = validated_values
            
            # Check all sensors have same length
            unique_lengths = set(lengths.values())
            if len(unique_lengths) != 1:
                raise InvalidFeatureValueError(
                    f"All sensors must have the same length: {lengths}",
                    equipment_type=machine
                )
            
            received_length = next(iter(unique_lengths))
            
            # Check window size
            if received_length < bundle.window_size:
                raise InsufficientAcquisitionError(
                    f"Insufficient measurements: got {received_length}, need {bundle.window_size}",
                    equipment_type=machine,
                    received=received_length,
                    required=bundle.window_size,
                    status="acquisition_continue"
                )
            
            if received_length > bundle.window_size:
                raise InvalidSeriesLengthError(
                    f"Too many measurements: got {received_length}, expected exactly {bundle.window_size}",
                    equipment_type=machine,
                    received=received_length,
                    required=bundle.window_size
                )
            
            return validated

    def predict(self, machine: str, sensor_data: Dict) -> Dict:
        """
        Make a prediction using raw sensor data.
        
        Args:
            machine: Equipment type
            sensor_data: Raw sensor measurements
            
        Returns:
            Prediction dictionary with class, confidence, probabilities, etc.
            
        Raises:
            ModelServiceError: If prediction fails
        """
        bundle = self.get_bundle(machine)
        
        # Validate sensor data
        validated_data = self._validate_sensor_data(machine, sensor_data)
        
        # Extract features using V7 feature extractor
        try:
            if machine == "moteur":
                features = FeatureExtractorV7.extract(machine, validated_data["vibration"])
            else:
                features = FeatureExtractorV7.extract(machine, validated_data)
        except Exception as exc:
            logger.error(f"Feature extraction failed for {machine}: {exc}")
            raise InvalidFeatureValueError(
                f"Feature extraction failed: {exc}",
                equipment_type=machine
            )
        
        # Validate feature count
        if len(features) != len(bundle.feature_names):
            raise InvalidBundleError(
                f"Feature count mismatch: extracted {len(features)}, expected {len(bundle.feature_names)}",
                equipment_type=machine
            )
        
        # Create feature array for prediction
        feature_array = features.reshape(1, -1)
        
        # Make prediction
        predicted_class_idx = bundle.model.predict(feature_array)[0]
        probabilities_array = bundle.model.predict_proba(feature_array)[0]
        
        # Map prediction to class label
        if isinstance(predicted_class_idx, (int, np.integer)):
            predicted_class = bundle.classes[int(predicted_class_idx)]
        else:
            predicted_class = str(predicted_class_idx)
        
        # Get probability labels
        model_classes = getattr(bundle.model, "classes_", None)
        if model_classes is not None:
            prob_labels = [bundle.classes[int(c)] if isinstance(c, (int, np.integer)) else str(c) 
                          for c in model_classes]
        else:
            prob_labels = list(bundle.classes)
        
        # Build probabilities dictionary
        probabilities = {label: float(prob) for label, prob in zip(prob_labels, probabilities_array)}
        confidence = probabilities.get(predicted_class, 0.0)
        defect_score = 1.0 - probabilities.get("normal_operation", 0.0)
        
        # Get recommendation
        recommendation_entry = self.recommendations.get(predicted_class, {})
        
        # Build result
        return {
            "equipment_type": bundle.machine,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities,
            "status": "normal" if predicted_class == "normal_operation" else "alerte",
            "recommendation": recommendation_entry.get("recommendation"),
            "recommendation_status": recommendation_entry.get("status"),
            "model_version": self.model_version,
            "model_release": bundle.version,
            "estimator_type": bundle.estimator_type,
            "feature_names": list(bundle.feature_names),
            "machine": bundle.machine,
            "defect": predicted_class,
            "defect_score": defect_score,
            "anomaly_score": defect_score,
            "defect_scores": probabilities,
            "required_sensors": list(bundle.raw_sensor_names),
            "window_size": bundle.window_size,
            "sampling_rate_hz": bundle.sampling_rate_hz,
        }

    def status(self) -> Dict:
        """Get status of all loaded models."""
        def _warnings(bundle: LoadedBundle) -> List[str]:
            warnings = [
                "Internal validation prototype - not industrial certification"
            ]
            
            if bundle.metrics.get("accuracy", 1.0) < 0.7:
                warnings.append("model_accuracy_below_0.70")
            
            report = bundle.metrics.get("classification_report", {})
            if any(isinstance(value, dict) and value.get("recall") == 0 for value in report.values()):
                warnings.append("at_least_one_class_has_zero_recall")
            
            provenance_text = " ".join(str(value).lower() for value in bundle.source_manifest.values())
            if "proxy" in provenance_text:
                warnings.append("proxy_label_mapping")
            if "simulation" in provenance_text:
                warnings.append("contains_simulated_training_data")
            
            return warnings
        
        return {
            name: {
                "model_version": self.model_version,
                "loaded": True,
                "version": bundle.version,
                "estimator_type": bundle.estimator_type,
                "classes": list(bundle.classes),
                "feature_count": len(bundle.feature_names),
                "raw_sensor_names": list(bundle.raw_sensor_names),
                "required_window_size": bundle.window_size,
                "sampling_rate_hz": bundle.sampling_rate_hz,
                "supported_input_types": ["series"],  # V7 only supports raw sensor series
                "clean_accuracy": bundle.metrics.get("clean_accuracy", bundle.metrics.get("accuracy")),
                "clean_macro_f1": bundle.metrics.get("clean_macro_f1", bundle.metrics.get("macro_f1")),
                "robustness_accuracy": bundle.metrics.get("robustness_accuracy", bundle.metrics.get("accuracy")),
                "robustness_macro_f1": bundle.metrics.get("robustness_macro_f1", bundle.metrics.get("macro_f1")),
                "robustness_noise_sigma": bundle.metrics.get("robustness_noise_sigma"),
                "robustness_repeats": bundle.metrics.get("robustness_repeats"),
                "minimum_class_recall": bundle.metrics.get("minimum_class_recall"),
                "evaluation_protocol": bundle.metrics.get("evaluation_protocol"),
                "feature_extractor_version": bundle.feature_extractor_version,
                "primary_metric": {
                    "label": "Robustness test result",
                    "accuracy": bundle.metrics.get("robustness_accuracy", bundle.metrics.get("accuracy")),
                },
                "clean_metric": {
                    "label": "Clean test result (unperturbed)",
                    "accuracy": bundle.metrics.get("clean_accuracy", bundle.metrics.get("accuracy")),
                },
                "warnings": _warnings(bundle),
                "provenance": bundle.source_manifest,
            }
            for name, bundle in self.bundles.items()
        }

    def predict_from_features(self, machine: str, features: Dict[str, float]) -> Dict:
        """
        Make a prediction using pre-computed features (for motor VBL features).
        
        Args:
            machine: Equipment type
            features: Dictionary of feature name -> value
            
        Returns:
            Prediction dictionary
            
        Raises:
            ModelServiceError: If prediction fails
        """
        bundle = self.get_bundle(machine)
        
        # Validate features
        missing = [name for name in bundle.feature_names if name not in features]
        if missing:
            raise MissingFeaturesError(
                f"Missing required features: {missing}",
                equipment_type=machine,
                missing=missing
            )
        
        # Extract features in correct order
        feature_array = np.array([
            self._validate_number(features[name], name) 
            for name in bundle.feature_names
        ]).reshape(1, -1)
        
        # Make prediction
        predicted_class_idx = bundle.model.predict(feature_array)[0]
        probabilities_array = bundle.model.predict_proba(feature_array)[0]
        
        # Map prediction to class label
        if isinstance(predicted_class_idx, (int, np.integer)):
            predicted_class = bundle.classes[int(predicted_class_idx)]
        else:
            predicted_class = str(predicted_class_idx)
        
        # Get probability labels
        model_classes = getattr(bundle.model, "classes_", None)
        if model_classes is not None:
            prob_labels = [bundle.classes[int(c)] if isinstance(c, (int, np.integer)) else str(c) 
                          for c in model_classes]
        else:
            prob_labels = list(bundle.classes)
        
        # Build probabilities dictionary
        probabilities = {label: float(prob) for label, prob in zip(prob_labels, probabilities_array)}
        confidence = probabilities.get(predicted_class, 0.0)
        defect_score = 1.0 - probabilities.get("normal_operation", 0.0)
        
        # Get recommendation
        recommendation_entry = self.recommendations.get(predicted_class, {})
        
        # Build result
        return {
            "equipment_type": bundle.machine,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities,
            "status": "normal" if predicted_class == "normal_operation" else "alerte",
            "recommendation": recommendation_entry.get("recommendation"),
            "recommendation_status": recommendation_entry.get("status"),
            "model_version": self.model_version,
            "model_release": bundle.version,
            "estimator_type": bundle.estimator_type,
            "feature_names": list(bundle.feature_names),
            "machine": bundle.machine,
            "defect": predicted_class,
            "defect_score": defect_score,
            "anomaly_score": defect_score,
            "defect_scores": probabilities,
            "required_sensors": ["features"],  # Pre-computed features
            "window_size": None,  # Not applicable for pre-computed features
            "sampling_rate_hz": None,  # Not applicable for pre-computed features
        }
