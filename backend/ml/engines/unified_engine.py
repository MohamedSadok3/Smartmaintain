"""ML prediction engine for V7 models."""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any

SERVICES_DIR = Path(__file__).resolve().parents[1] / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from model_service import ModelService, ModelServiceError

logger = logging.getLogger(__name__)


class MLEngine:
    """
    ML engine for V7 models.
    
    V7 models accept raw sensor series with simplified input contracts.
    Feature extraction is performed automatically by the model service.
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        recommendations_path: Optional[str] = None
    ):
        """
        Initialize ML engine with V7 models.
        
        Args:
            models_dir: Path to V7 models directory
            recommendations_path: Path to recommendations.json
        """
        try:
            self.service = ModelService(
                models_dir=models_dir,
                recommendations_path=recommendations_path
            )
            logger.info("V7 models loaded successfully")
        except Exception as exc:
            logger.exception("Failed to load V7 models")
            raise RuntimeError(f"Failed to load V7 models: {exc}")
        
        logger.info("MLEngine initialized")
    
    def predict(
        self,
        machine: str,
        sensors: Dict[str, Any]
    ) -> Dict:
        """
        Make a prediction for the given machine and sensor data.
        
        Args:
            machine: Equipment type (moteur, pompe, compresseur, echangeur)
            sensors: Raw sensor data dict
                Standard format: {"sensor_name": [values...], ...}
                Motor format: {"features": {...}} for pre-computed VBL features
            
        Returns:
            Prediction dictionary with health_index, defect, recommendation, etc.
            
        Raises:
            ModelServiceError: If prediction fails
        """
        try:
            # Remove wrapper if present
            if isinstance(sensors, dict) and "series" in sensors:
                sensor_data = sensors["series"]
            elif isinstance(sensors, dict) and "sensors" in sensors:
                sensor_data = sensors["sensors"]
            else:
                sensor_data = sensors
            
            # Special case: Motor with pre-computed features
            if machine == "moteur" and isinstance(sensor_data, dict) and "features" in sensor_data:
                # Motor features already computed (VBL features), use directly
                return self.service.predict_from_features(machine, sensor_data["features"])
            
            return self.service.predict(machine, sensor_data)
            
        except ModelServiceError:
            # Re-raise model service errors as-is
            raise
        except Exception as exc:
            logger.exception(f"Prediction failed for {machine}")
            raise ModelServiceError(f"Prediction failed for {machine}: {exc}")
    
    def get_status(self) -> Dict:
        """
        Get status of loaded models.
        
        Returns:
            Status dictionary with loaded bundles
        """
        return {
            "model_version": "v7",
            "bundles": self.service.status(),
        }
    
    def get_bundle(self, machine: str):
        """Get model bundle for specified machine."""
        return self.service.get_bundle(machine)
    
    # Compatibility properties
    @property
    def model_service(self):
        """Get model service."""
        return self.service
    
    @property
    def models(self):
        """Get models dict."""
        if hasattr(self.service, 'bundles'):
            return {name: bundle.model for name, bundle in self.service.bundles.items()}
        return {}
    
    @property
    def metadata(self):
        """Get metadata dict."""
        if hasattr(self.service, 'bundles'):
            return {name: bundle.metadata for name, bundle in self.service.bundles.items()}
        return {}


# Alias for backward compatibility
UnifiedMLEngine = MLEngine
